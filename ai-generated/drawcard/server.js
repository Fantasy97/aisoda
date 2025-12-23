const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const { GameEngine } = require('./game-engine');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// 静态文件服务
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

// 游戏引擎实例
const gameEngine = new GameEngine();

// 路由
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API路由
app.post('/api/init-game', (req, res) => {
    const { playerNames } = req.body;
    const gameState = gameEngine.initializeGame(playerNames);
    io.emit('gameStateUpdate', gameState);
    res.json({ success: true, gameState });
});

app.post('/api/place-bid', (req, res) => {
    const { playerId, amount } = req.body;
    const result = gameEngine.placeBid(playerId, amount);
    if (result.success) {
        io.emit('gameStateUpdate', result.gameState);
    }
    res.json(result);
});

app.post('/api/draw-cards', (req, res) => {
    const { playerId } = req.body;
    const result = gameEngine.drawCards(playerId);
    if (result.success) {
        io.emit('gameStateUpdate', result.gameState);
        io.emit('cardsDrawn', { playerId, cards: result.cards });
    }
    res.json(result);
});

app.post('/api/flip-cards', (req, res) => {
    const { playerId, cardIds } = req.body;
    const result = gameEngine.flipCards(playerId, cardIds);
    if (result.success) {
        io.emit('gameStateUpdate', result.gameState);
        io.emit('cardsFlipped', { 
            playerId, 
            results: result.results, 
            triggeredBomb: result.triggeredBomb 
        });
    }
    res.json(result);
});

app.post('/api/leave-game', (req, res) => {
    const { playerId } = req.body;
    const result = gameEngine.leaveGame(playerId);
    
    if (result.success) {
        io.emit('gameStateUpdate', result.gameState);
        io.emit('playerLeft', { playerId });
    }
    
    res.json(result);
});

app.post('/api/end-flipping', (req, res) => {
    const { playerId } = req.body;
    const result = gameEngine.endFlipping(playerId);
    
    if (result.success) {
        io.emit('gameStateUpdate', result.gameState);
    }
    
    res.json(result);
});

app.get('/api/player-cards/:playerId', (req, res) => {
    const { playerId } = req.params;
    const player = gameEngine.players.find(p => p.id === playerId);
    
    if (!player || !player.currentRoundCards || player.currentRoundCards.length === 0) {
        return res.json({ success: false, message: '玩家未抽牌或无抽牌记录' });
    }
    
    // 获取玩家本轮抽到的牌
    const cards = player.currentRoundCards.map(cardId => {
        const card = gameEngine.cardDeck.find(c => c.id === cardId);
        if (!card) return null;
        
        return {
            id: card.id,
            type: card.isFlipped ? card.type : 'hidden',
            value: card.isFlipped ? card.currentValue : undefined,
            originalOwner: card.originalOwner // 始终显示原主人信息，但不影响翻牌结果归属
        };
    }).filter(card => card !== null);
    
    res.json({ success: true, cards });
});

app.post('/api/reset-game', (req, res) => {
    gameEngine.resetGame();
    const gameState = gameEngine.getGameState();
    io.emit('gameStateUpdate', gameState);
    res.json({ success: true, gameState });
});

// 调试API
app.post('/api/debug/adjust-player', (req, res) => {
    const { playerId, adjustments } = req.body;
    const result = gameEngine.adjustPlayerValues(playerId, adjustments);
    if (result.success) {
        const gameState = gameEngine.getGameState();
        io.emit('gameStateUpdate', gameState);
    }
    res.json(result);
});

app.post('/api/debug/set-deck', (req, res) => {
    const { cards } = req.body;
    const result = gameEngine.setCardDeck(cards);
    if (result.success) {
        const gameState = gameEngine.getGameState();
        io.emit('gameStateUpdate', gameState);
    }
    res.json(result);
});

app.get('/api/game-state', (req, res) => {
    res.json(gameEngine.getGameState());
});

// Socket.IO连接处理
io.on('connection', (socket) => {
    console.log('客户端已连接:', socket.id);
    
    // 发送当前游戏状态
    socket.emit('gameStateUpdate', gameEngine.getGameState());
    
    socket.on('disconnect', () => {
        console.log('客户端已断开:', socket.id);
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`游戏服务器运行在 http://localhost:${PORT}`);
});

module.exports = { app, server, gameEngine };
