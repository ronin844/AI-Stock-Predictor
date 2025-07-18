import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { useNavigate, Navigate } from 'react-router-dom';
import {
  Box,
  Container,
  TextField,
  Button,
  Typography,
  Paper,
  Alert,
  Checkbox,
  FormControlLabel,
  Link,
  Divider,
  IconButton,
  InputAdornment,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';

function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const auth = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  if (auth.isAuthenticated) {
    return <Navigate to="/" />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      console.log('Login form submitted with:', { username, password });
      await auth.login(username, password);
      navigate('/');
    } catch (err) {
      console.error('Login form error:', err);
      setError(err.message || 'Invalid credentials. Please try again.');
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0061f2 0%, #0044ab 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
        padding: { xs: 2, sm: 3, md: 4 },
      }}
    >
      {/* Decorative circles */}
      <Box
        sx={{
          position: 'absolute',
          width: { xs: '150px', sm: '200px', md: '300px' },
          height: { xs: '150px', sm: '200px', md: '300px' },
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.1)',
          left: { xs: '-75px', sm: '-100px', md: '-150px' },
          bottom: { xs: '-75px', sm: '-100px', md: '-150px' },
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          width: { xs: '100px', sm: '150px', md: '200px' },
          height: { xs: '100px', sm: '150px', md: '200px' },
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.1)',
          right: { xs: '5%', sm: '8%', md: '10%' },
          top: { xs: '5%', sm: '8%', md: '10%' },
        }}
      />

      <Container maxWidth="lg" sx={{ width: '100%' }}>
        <Paper
          elevation={24}
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', md: 'row' },
            borderRadius: { xs: '15px', md: '20px' },
            overflow: 'hidden',
            minHeight: { xs: 'auto', md: '600px' },
            maxWidth: { xs: '100%', sm: '500px', md: '1000px' },
            margin: '0 auto',
          }}
        >
          {/* Left side - Welcome */}
          <Box
            sx={{
              flex: { xs: 'none', md: 1 },
              background: 'linear-gradient(135deg, #0061f2 0%, #0044ab 100%)',
              color: 'white',
              padding: { xs: 4, sm: 6, md: 8 },
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              minHeight: { xs: '200px', md: 'auto' },
              textAlign: { xs: 'center', md: 'left' },
            }}
          >
            <Typography
              variant={isMobile ? 'h3' : 'h2'}
              component="h1"
              sx={{
                fontWeight: 700,
                mb: 2,
                fontSize: { xs: '2rem', sm: '2.5rem', md: '3.75rem' }
              }}
            >
              WELCOME
            </Typography>
            <Typography
              variant={isMobile ? 'h5' : 'h4'}
              sx={{
                mb: { xs: 2, md: 4 },
                fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2.125rem' }
              }}
            >
              AI Stock Predictor
            </Typography>
            <Typography
              variant="body1"
              sx={{
                opacity: 0.8,
                fontSize: { xs: '0.875rem', sm: '1rem' }
              }}
            >
              Predict stock levels and optimize inventory management with AI
            </Typography>
          </Box>

          {/* Right side - Sign in form */}
          <Box
            sx={{
              flex: { xs: 'none', md: 1 },
              bgcolor: 'background.paper',
              padding: { xs: 4, sm: 6, md: 8 },
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              minWidth: { xs: '100%', md: '400px' },
            }}
          >
            <Typography
              variant={isMobile ? 'h5' : 'h4'}
              component="h2"
              sx={{
                mb: { xs: 3, md: 4 },
                textAlign: { xs: 'center', md: 'left' },
                fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2.125rem' }
              }}
            >
              Sign in
            </Typography>
            <Box component="form" onSubmit={handleSubmit}>
              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}
              <TextField
                fullWidth
                label="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                variant="outlined"
                sx={{
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '10px',
                    backgroundColor: 'rgba(0, 0, 0, 0.03)',
                    '& fieldset': {
                      border: '1px solid rgba(0, 0, 0, 0.15)',
                    },
                    '&:hover fieldset': {
                      borderColor: '#0061f2',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#0061f2',
                    },
                  },
                }}
                InputProps={{
                  style: { color: '#000' }
                }}
              />
              <TextField
                fullWidth
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                variant="outlined"
                sx={{
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '10px',
                    backgroundColor: 'rgba(0, 0, 0, 0.03)',
                    '& fieldset': {
                      border: '1px solid rgba(0, 0, 0, 0.15)',
                    },
                    '&:hover fieldset': {
                      borderColor: '#0061f2',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#0061f2',
                    },
                  },
                }}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                        sx={{ color: '#0061f2' }}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />

              <Box sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                justifyContent: 'space-between',
                alignItems: { xs: 'flex-start', sm: 'center' },
                mb: 3,
                gap: { xs: 1, sm: 0 }
              }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                    />
                  }
                  label="Remember me"
                />
                <Link href="#" underline="hover">
                  Forgot Password?
                </Link>
              </Box>
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                sx={{
                  mb: 3,
                  bgcolor: '#0061f2',
                  '&:hover': { bgcolor: '#0044ab' },
                  height: { xs: '48px', md: '56px' },
                }}
              >
                Sign in
              </Button>
              <Divider sx={{ mb: 3 }}>or</Divider>
              <Button
                fullWidth
                variant="outlined"
                size="large"
                sx={{
                  mb: 3,
                  height: { xs: '48px', md: '56px' },
                }}
              >
                
              </Button>
             
            </Box>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}

export default LoginPage;
