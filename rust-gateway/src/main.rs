use actix::prelude::*;
use actix_cors::Cors;
use actix_web::{get, http, post, web, App, Error, HttpRequest, HttpResponse, HttpServer, Responder};
use actix_web_actors::ws;
use chrono::Utc;
use jsonwebtoken::{decode, encode, Algorithm, DecodingKey, EncodingKey, Header, TokenData, Validation};
use rand::{self, Rng};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::HashMap;
use std::time::Instant;

// ---------------------- 1. DEFINE WEBSOCKET MESSAGES ----------------------

#[derive(Message)]
#[rtype(result = "()")]
pub struct BroadcastMessage(pub String);

#[derive(Message)]
#[rtype(usize)]
pub struct Connect {
    pub addr: Recipient<BroadcastMessage>,
}

#[derive(Message)]
#[rtype(result = "()")]
pub struct Disconnect {
    pub id: usize,
}

#[derive(Message)]
#[rtype(result = "()")]
pub struct ClientMessage {
    pub msg: String,
}

// ---------------------- 2. DEFINE LOBBY (BROADCASTER) ACTOR ----------------------

#[derive(Debug)]
pub struct Lobby {
    sessions: HashMap<usize, Recipient<BroadcastMessage>>,
    rng: rand::rngs::ThreadRng,
}

impl Lobby {
    pub fn new() -> Lobby {
        Lobby {
            sessions: HashMap::new(),
            rng: rand::thread_rng(),
        }
    }
}

impl Actor for Lobby {
    type Context = Context<Self>;
}

impl Handler<Connect> for Lobby {
    type Result = usize;

    fn handle(&mut self, msg: Connect, _: &mut Self::Context) -> Self::Result {
        // FIX #1: Use raw identifier r#gen to avoid keyword conflict
        let id = self.rng.r#gen::<usize>();
        println!("Someone joined lobby with id {}", id);
        self.sessions.insert(id, msg.addr);
        id
    }
}

impl Handler<Disconnect> for Lobby {
    type Result = ();

    fn handle(&mut self, msg: Disconnect, _: &mut Self::Context) {
        println!("Someone with id {} disconnected", msg.id);
        self.sessions.remove(&msg.id);
    }
}

impl Handler<ClientMessage> for Lobby {
    type Result = ();

    fn handle(&mut self, msg: ClientMessage, _: &mut Self::Context) {
        println!("Lobby received message to broadcast: {}", msg.msg);
        for (_id, addr) in self.sessions.iter() {
            let _ = addr.do_send(BroadcastMessage(msg.msg.clone()));
        }
    }
}

// ---------------------- 3. DEFINE WEBSOCKET SESSION ACTOR ----------------------

pub struct MyWebSocket {
    id: usize,
    hb: Instant,
    lobby_addr: Addr<Lobby>,
}

impl MyWebSocket {
    pub fn new(lobby_addr: Addr<Lobby>) -> Self {
        Self {
            id: 0,
            hb: Instant::now(),
            lobby_addr,
        }
    }
}

impl Actor for MyWebSocket {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        let addr = ctx.address();
        self.lobby_addr
            .send(Connect {
                addr: addr.recipient(),
            })
            .into_actor(self)
            .then(|res, act, ctx| {
                match res {
                    Ok(res) => act.id = res,
                    _ => ctx.stop(),
                }
                fut::ready(())
            })
            .wait(ctx);
    }

    fn stopping(&mut self, _: &mut Self::Context) -> Running {
        self.lobby_addr.do_send(Disconnect { id: self.id });
        Running::Stop
    }
}

impl Handler<BroadcastMessage> for MyWebSocket {
    type Result = ();

    fn handle(&mut self, msg: BroadcastMessage, ctx: &mut Self::Context) {
        ctx.text(msg.0);
    }
}

impl StreamHandler<Result<ws::Message, ws::ProtocolError>> for MyWebSocket {
    fn handle(&mut self, msg: Result<ws::Message, ws::ProtocolError>, ctx: &mut Self::Context) {
        match msg {
            Ok(ws::Message::Ping(msg)) => {
                self.hb = Instant::now();
                ctx.pong(&msg);
            }
            Ok(ws::Message::Pong(_)) => {
                self.hb = Instant::now();
            }
            Ok(ws::Message::Close(reason)) => {
                ctx.close(reason);
                ctx.stop();
            }
            Ok(ws::Message::Text(_text)) => (),
            _ => ctx.stop(),
        }
    }
}

// ---------------------- 4. DEFINE ROUTES ----------------------

#[get("/ws")]
async fn websocket_route(
    req: HttpRequest,
    stream: web::Payload,
    lobby: web::Data<Addr<Lobby>>,
) -> Result<HttpResponse, Error> {
    ws::start(MyWebSocket::new(lobby.get_ref().clone()), &req, stream)
}

#[get("/")]
async fn hello() -> impl Responder {
    HttpResponse::Ok().body("Edge Retail gateway running")
}

#[derive(Debug, Deserialize)]
struct AuthRequest {
    username: String,
    password: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct AuthClaims {
    sub: String,
    exp: usize,
    role: String,
}

#[post("/auth/token")]
async fn get_token(
    body: web::Json<AuthRequest>,
    lobby: web::Data<Addr<Lobby>>,
) -> impl Responder {
    let AuthRequest { username, password } = body.into_inner();

    let (valid_user, role) = match (username.as_str(), password.as_str()) {
        ("admin", "password123") => (true, "admin"),
        ("viewer", "viewerpass") => (true, "viewer"),
        _ => (false, ""),
    };

    if valid_user {
        lobby.do_send(ClientMessage {
            msg: format!("AUTH: User '{}' logged in with role '{}'", &username, role),
        });

        let expiration = Utc::now()
            .checked_add_signed(chrono::Duration::minutes(60))
            .unwrap()
            .timestamp() as usize;

        let claims = AuthClaims {
            sub: username.clone(),
            exp: expiration,
            role: role.to_string(),
        };
        let secret = b"a-string-secret-at-least-256-bits-long";

        match encode(&Header::default(), &claims, &EncodingKey::from_secret(secret)) {
            Ok(token) => HttpResponse::Ok().json(json!({ "token": token })),
            Err(_) => HttpResponse::InternalServerError().body("Token generation failed"),
        }
    } else {
        HttpResponse::Unauthorized().body("Invalid credentials")
    }
}

fn validate_jwt(req: &HttpRequest) -> Result<TokenData<AuthClaims>, HttpResponse> {
    let auth_header = match req.headers().get("Authorization") {
        Some(h) => h.to_str().unwrap_or(""),
        None => return Err(HttpResponse::Unauthorized().body("Missing Authorization header")),
    };

    if !auth_header.starts_with("Bearer ") {
        return Err(HttpResponse::Unauthorized().body("Invalid token format"));
    }

    let token = &auth_header[7..];
    let secret = b"a-string-secret-at-least-256-bits-long";
    let decoded = decode::<AuthClaims>(
        token,
        &DecodingKey::from_secret(secret),
        &Validation::new(Algorithm::HS256),
    );

    match decoded {
        Ok(data) => Ok(data),
        Err(_) => Err(HttpResponse::Unauthorized().body("Invalid or expired token")),
    }
}

#[derive(Debug, Deserialize, Clone)]
struct InventoryItem {
    product_id: String,
    quantity: u32,
    location: String,
}

#[post("/inventory")]
async fn handle_inventory(
    req: HttpRequest,
    item: web::Json<InventoryItem>,
    lobby: web::Data<Addr<Lobby>>,
) -> impl Responder {
    match validate_jwt(&req) {
        Ok(token_data) => {
            if token_data.claims.role != "admin" {
                return HttpResponse::Forbidden().body("Access denied");
            }

            let item_clone = item.clone();
            lobby.do_send(ClientMessage {
                msg: format!(
                    "INVENTORY: '{}' updated product '{}' in '{}' to quantity {}",
                    token_data.claims.sub, item_clone.product_id, item_clone.location, item_clone.quantity
                ),
            });

            println!("✅ Authenticated: {}", token_data.claims.sub);
            println!("📦 Inventory received: {:?}", item);

            HttpResponse::Ok().body("Inventory received securely")
        }
        Err(error_response) => error_response,
    }
}

#[get("/inventory/view")]
async fn view_inventory(req: HttpRequest) -> impl Responder {
    match validate_jwt(&req) {
        Ok(token_data) => match token_data.claims.role.as_str() {
            "admin" | "viewer" => {
                println!("🔍 View access granted for: {}", token_data.claims.sub);
                // Updated to match the data structure expected by the MUI DataGrid on the frontend
                HttpResponse::Ok().json(json!([
                    { "id": "P101", "product_id": "P101", "quantity": 50, "location": "Delhi", "low_stock": false },
                    { "id": "P102", "product_id": "P102", "quantity": 100, "location": "Mumbai", "low_stock": false },
                    { "id": "P103", "product_id": "P103", "quantity": 15, "location": "Delhi", "low_stock": true },
                    { "id": "P104", "product_id": "P104", "quantity": 200, "location": "Bangalore", "low_stock": false },
                ]))
            }
            _ => HttpResponse::Forbidden().body("Access denied"),
        },
        Err(error_response) => error_response,
    }
}

#[derive(Serialize, Deserialize, Clone)]
struct PredictionRequest {
    product_id: String,
    store_id: String,
}

// FIX #2: Add Serialize to the derive macro
#[derive(Serialize, Deserialize)]
struct PredictionResponse {
    store_id: String,
    product_id: String,
    current_stock: u32,
    predicted_demand: u32,
    status: String,
    daily_forecast: Vec<f32>,
}

#[post("/demand/forecast")]
async fn demand_forecast(
    req: HttpRequest,
    payload: web::Json<PredictionRequest>,
    lobby: web::Data<Addr<Lobby>>,
) -> impl Responder {
    match validate_jwt(&req) {
        Ok(token_data) => {
            if token_data.claims.role != "admin" {
                return HttpResponse::Forbidden().body("Only admins can forecast demand");
            }

            let payload_clone = payload.clone();
            lobby.do_send(ClientMessage {
                msg: format!(
                    "FORECAST: '{}' requested forecast for product '{}' in store '{}'",
                    token_data.claims.sub, payload_clone.product_id, payload_clone.store_id,
                ),
            });

            let client = Client::new();
            let url = "https://6e60-2401-4900-8848-61f6-3a-a495-c558-9484.ngrok-free.app/predict";

            let resp = client.post(url).json(&*payload).send().await;

            match resp {
                Ok(response) => {
                    if response.status().is_success() {
                        match response.json::<PredictionResponse>().await {
                            Ok(p) => HttpResponse::Ok().json(p), // Send the struct directly
                            Err(e) => HttpResponse::InternalServerError().body(format!("Failed to parse response: {}", e)),
                        }
                    } else {
                        let status = response.status();
                        let body = response.text().await.unwrap_or_else(|_| "Could not read error body".to_string());
                        let actix_status = http::StatusCode::from_u16(status.as_u16()).unwrap_or(http::StatusCode::INTERNAL_SERVER_ERROR);
                        HttpResponse::build(actix_status).body(format!("Model service error: {}", body))
                    }
                }
                Err(e) => HttpResponse::InternalServerError().body(format!("Failed to reach AI model: {}", e)),
            }
        }
        Err(err_response) => err_response,
    }
}

// ---------------------- 5. CONFIGURE AND START SERVER ----------------------
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("🚀 Starting server on http://127.0.0.1:8000");

    let lobby = Lobby::new().start();

    HttpServer::new(move || {
        let cors = Cors::default()
            .allowed_origin("http://localhost:3000")
            .allowed_origin("http://localhost:3001")
            .allowed_methods(vec!["GET", "POST"])
            .allowed_headers(vec![
                http::header::AUTHORIZATION,
                http::header::ACCEPT,
                http::header::CONTENT_TYPE,
            ])
            .supports_credentials()
            .max_age(3600);

        App::new()
            .wrap(cors)
            .app_data(web::Data::new(lobby.clone()))
            .service(hello)
            .service(get_token)
            .service(handle_inventory)
            .service(view_inventory)
            .service(demand_forecast)
            .service(websocket_route)
    })
    .bind(("127.0.0.1", 8088))?
    .run()
    .await
}
