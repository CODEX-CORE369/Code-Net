const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));

// MongoDB Connection
mongoose.connect("mongodb+srv://dxsimu:mnbvcxzdx@dxsimu.0qrxmsr.mongodb.net/CODE-NET")
  .then(() => console.log('>> DATABASE_CONNECTED_SUCCESSFULLY'))
  .catch(err => console.log(err));

// --- SCHEMAS ---
const UserSchema = new mongoose.Schema({
  username: String,
  password: { type: String, select: false },
  icon: { type: String, default: 'https://i.ibb.co/mR49v81/default-avatar.png' },
  role: { type: String, default: 'user' },
  level: { type: String, default: 'NOOB' },
  bio: { type: String, default: 'System user of Code-Net' }
});

const PostSchema = new mongoose.Schema({
  username: String,
  userIcon: String,
  type: String, // 'text', 'image', 'video'
  content: String,
  mediaUrl: String,
  likes: { type: [String], default: [] }, // Array of usernames
  comments: [{ username: String, text: String, date: { type: Date, default: Date.now } }],
  timestamp: { type: Date, default: Date.now }
});

const User = mongoose.model('User', UserSchema);
const Post = mongoose.model('Post', PostSchema);

// --- ROUTES ---

// Login & Fetch Profile
app.post('/api/login', async (req, res) => {
    const { username, password } = req.body;
    const user = await User.findOne({ username, password: password });
    if (!user) return res.status(401).json({ error: 'INVALID_CREDENTIALS' });
    res.json(user);
});

// Posts with Real-time logic
app.get('/api/posts', async (req, res) => {
    const posts = await Post.find().sort({ timestamp: -1 });
    res.json(posts);
});

app.post('/api/posts', async (req, res) => {
    const newPost = new Post(req.body);
    await newPost.save();
    res.json(newPost);
});

// Like System (No Refresh Logic)
app.post('/api/posts/:id/like', async (req, res) => {
    const { username } = req.body;
    const post = await Post.findById(req.params.id);
    if (post.likes.includes(username)) {
        post.likes = post.likes.filter(u => u !== username);
    } else {
        post.likes.push(username);
    }
    await post.save();
    res.json({ likes: post.likes.length, liked: post.likes.includes(username) });
});

// Comment System
app.post('/api/posts/:id/comment', async (req, res) => {
    const post = await Post.findById(req.params.id);
    post.comments.push(req.body);
    await post.save();
    res.json(post.comments);
});

// Delete Post
app.delete('/api/posts/:id', async (req, res) => {
    await Post.findByIdAndDelete(req.params.id);
    res.json({ success: true });
});

app.listen(3000, () => console.log('>> SERVER_STABLE_ON_PORT_3000'));
