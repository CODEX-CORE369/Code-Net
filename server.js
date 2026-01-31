const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json({ limit: '50mb' }));

// MongoDB Connection
const MONGO_URI = "mongodb+srv://dxsimu:mnbvcxzdx@dxsimu.0qrxmsr.mongodb.net/CODE-NET?appName=dxsimu";
mongoose.connect(MONGO_URI)
  .then(() => console.log('>> MongoDB Connected (CODE-NET)'))
  .catch(err => console.error('>> MongoDB Connection Error:', err));

// --- SCHEMAS ---
const UserSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  icon: String,
  role: { type: String, default: 'user' }, // 'admin' or 'user'
  isBanned: { type: Boolean, default: false },
  banExpires: { type: Date, default: null },
  ip: { type: String, default: '' } // Stores last login IP
});

const PostSchema = new mongoose.Schema({
  username: String,
  type: String, // 'text', 'image', 'video', 'ad'
  content: String,
  mediaUrl: String,
  timestamp: { type: Date, default: Date.now },
  likes: [String],
  comments: [{ username: String, text: String, timestamp: Date }]
});

const User = mongoose.model('User', UserSchema);
const Post = mongoose.model('Post', PostSchema);

// --- KEEP ALIVE ---
const KEEP_ALIVE_INTERVAL = 5 * 60 * 1000;
app.get('/ping', (req, res) => res.send('Pong!'));
function keepServerAlive() {
  if(process.env.RENDER_EXTERNAL_URL) {
      setInterval(async () => {
        try { await axios.get(`${process.env.RENDER_EXTERNAL_URL}/ping`); } 
        catch (e) { console.log('Ping failed'); }
      }, KEEP_ALIVE_INTERVAL);
  }
}
keepServerAlive();

// --- ROUTES ---

// 1. Register (Creates User)
app.post('/api/register', async (req, res) => {
  try {
    const { username, password, icon } = req.body;
    const existingUser = await User.findOne({ username });
    if (existingUser) return res.status(400).json({ message: 'Username taken' });

    // IP Capture
    const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;

    const newUser = new User({ username, password, icon, ip });
    await newUser.save();
    res.json({ success: true, message: 'Account created' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 2. Login (Checks Ban & Updates IP)
app.post('/api/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    const user = await User.findOne({ username, password });
    
    if (!user) return res.status(400).json({ message: 'Invalid credentials' });

    // Check Ban Status
    if (user.isBanned) {
      if (user.banExpires && new Date() > user.banExpires) {
        user.isBanned = false;
        user.banExpires = null;
        await user.save();
      } else {
        return res.status(403).json({ 
            message: 'ACCOUNT BANNED', 
            expires: user.banExpires ? user.banExpires : 'PERMANENT' 
        });
      }
    }

    // Update IP
    user.ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    await user.save();

    res.json({ success: true, user });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 3. General Post Routes
app.get('/api/posts', async (req, res) => {
  const posts = await Post.find().sort({ timestamp: -1 });
  res.json(posts);
});

app.post('/api/posts', async (req, res) => {
  try {
    const newPost = new Post(req.body);
    await newPost.save();
    res.json(newPost);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.delete('/api/posts/:id', async (req, res) => {
    await Post.findByIdAndDelete(req.params.id);
    res.json({ success: true });
});

// --- ADMIN ROUTES ---

// Admin Login
app.post('/api/admin/login', async (req, res) => {
    const { username, password } = req.body;
    const user = await User.findOne({ username, password });
    if (!user || user.role !== 'admin') {
        return res.status(403).json({ message: 'ACCESS DENIED: NOT ADMIN' });
    }
    res.json({ success: true, user });
});

// Ban User
app.post('/api/admin/ban', async (req, res) => {
    const { username, duration } = req.body; // duration in days (0 for permanent)
    const user = await User.findOne({ username });
    if(!user) return res.status(404).json({ message: 'User not found' });

    user.isBanned = true;
    if (duration > 0) {
        const date = new Date();
        date.setDate(date.getDate() + parseInt(duration));
        user.banExpires = date;
    } else {
        user.banExpires = null; // Permanent
    }
    await user.save();
    res.json({ success: true, message: `User ${username} banned.` });
});

// Permanent Ban (Delete Account)
app.delete('/api/admin/user/:username', async (req, res) => {
    try {
        await User.findOneAndDelete({ username: req.params.username });
        await Post.deleteMany({ username: req.params.username }); // Delete their posts too
        res.json({ success: true, message: 'User and data terminated.' });
    } catch(err) { res.status(500).json({ error: err.message }); }
});

// Get IP
app.get('/api/admin/ip/:username', async (req, res) => {
    const user = await User.findOne({ username: req.params.username });
    if(!user) return res.status(404).json({ message: 'User not found' });
    res.json({ ip: user.ip });
});

// Search
app.get('/api/admin/search', async (req, res) => {
    const { query, type } = req.query;
    if(type === 'user') {
        const users = await User.find({ username: new RegExp(query, 'i') });
        res.json({ type: 'user', data: users });
    } else {
        const posts = await Post.find({ content: new RegExp(query, 'i') });
        res.json({ type: 'post', data: posts });
    }
});

// User Profile Check
app.get('/api/admin/user-details/:username', async (req, res) => {
    const user = await User.findOne({ username: req.params.username });
    if(!user) return res.status(404).json({ message: 'User not found' });
    const posts = await Post.find({ username: req.params.username });
    res.json({ user, posts });
});

app.listen(PORT, () => console.log(`>> Server running on ${PORT}`));
