const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'fallback-secret-dev-only';

// Middleware
app.use(cors());
app.use(express.json());

// ============================
// Microservices URLs
// ============================
const services = {
  'user-service': process.env.USER_SERVICE_URL,
  'wallet-service': process.env.WALLET_SERVICE_URL,
  'payment-service': process.env.PAYMENT_SERVICE_URL,
  'notification-service': process.env.NOTIFICATION_SERVICE_URL
};

// ============================
// Dummy User (for demo login)
// password: admin123
// ============================
const users = [
  {
    id: 1,
    username: 'user1',
    passwordHash: '$2a$10$BQW5aPyqYtasLrIMq8l6sOv/.IAfO23lGGV//tTQcrEjr.kqCeRCC',
    role: 'user'
  },
  {
    id: 2,
    username: 'admin',
    passwordHash: '$2a$10$BQW5aPyqYtasLrIMq8l6sOv/.IAfO23lGGV//tTQcrEjr.kqCeRCC',
    role: 'admin'
  }
];

// ============================
// Authentication Route
// ============================
app.post('/auth/login', async (req, res) => {
  const { username, password } = req.body;

  const user = users.find(u => u.username === username);
  if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
    return res.status(401).json({ error: "Invalid username or password" });
  }

  const token = jwt.sign(
    {
      id: user.id,
      username: user.username,
      role: user.role
    },
    JWT_SECRET,
    { expiresIn: '24h' }
  );

  return res.json({
    success: true,
    token,
    user: {
      id: user.id,
      username: user.username,
      role: user.role
    }
  });
});

// ============================
// JWT Middleware
// ============================
const authenticateJWT = (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({
      error: "Access denied. Token missing or incorrect format."
    });
  }

  const token = authHeader.split(" ")[1];

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded; 
    next();
  } catch (err) {
    return res.status(403).json({ error: "Invalid or expired token" });
  }
};

// ============================
// Proxy Generator
// Sends user ID, role, username to microservices
// ============================
const createAuthProxy = (serviceName) => {
  return createProxyMiddleware({
    target: services[serviceName],
    changeOrigin: true,
    pathRewrite: {
      [`^/api/${serviceName}`]: '' 
    },
    onProxyReq: (proxyReq, req) => {
      if (req.user) {
        proxyReq.setHeader("X-User-Id", req.user.id);
        proxyReq.setHeader("X-User-Username", req.user.username);
        proxyReq.setHeader("X-User-Role", req.user.role);
      }
    }
  });
};

// ============================
// Protected API Routes
// ============================
app.use('/api/user-service', authenticateJWT, createAuthProxy('user-service'));
app.use('/api/wallet-service', authenticateJWT, createAuthProxy('wallet-service'));
app.use('/api/payment-service', authenticateJWT, createAuthProxy('transaction-service'));
app.use('/api/notification-service', authenticateJWT, createAuthProxy('notification-service'));

// ============================
// Health Check
// ============================
app.get('/health', (req, res) => {
  res.json({ status: "OK", system: "Digital E-Wallet API Gateway", timestamp: new Date() });
});

// Start Server
app.listen(PORT, () => {
  console.log(`🚀 API Gateway running at http://localhost:${PORT}`);
  console.log(`🔐 Login: POST http://localhost:${PORT}/auth/login`);
});
