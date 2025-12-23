const { v4: uuidv4 } = require('uuid');

class Card {
    constructor(id, type, value, originalOwner = null) {
        this.id = id;
        this.type = type; // 'value' | 'bomb' | 'system_value' | 'system_bomb'
        this.originalValue = value;
        this.currentValue = value;
        this.isFlipped = false;
        this.originalOwner = originalOwner;
    }

    flip() {
        this.isFlipped = true;
        if (this.type === 'value' || this.type === 'system_value') {
            this.currentValue = 0; // 价值牌翻开后价值归零
        }
        return this.originalValue;
    }

    // 重置牌的状态（还牌时使用）
    resetFlipState() {
        // 注意：价值牌一旦被翻开，价值就永久归零，不会恢复
        // 重置翻牌标记，让牌可以重新被抽取，但不重置价值
        this.isFlipped = false;
    }

    copy() {
        return new Card(uuidv4(), this.type, this.originalValue, this.originalOwner);
    }
}

class Player {
    constructor(id, name) {
        this.id = id;
        this.name = name;
        this.role = 'farmer'; // 'farmer' | 'landlord'
        this.handCards = [];
        this.drawnCards = new Set(); // 已抽过的牌ID
        this.currentRoundCards = []; // 本轮抽到的牌ID
        this.isActive = true;
        this.roundCount = 0;
        this.bidAmount = 0;
        this.entryFee = 100;
    }

    addCardToHand(card) {
        this.handCards.push(card.copy());
    }

    getHandValue() {
        return this.handCards.reduce((total, card) => {
            if (card.type === 'value' || card.type === 'system_value') {
                return total + card.originalValue;
            }
            return total;
        }, 0);
    }

    getFinalScore() {
        if (this.role === 'landlord') {
            // 地主收益 = 牌库剩余价值 - 入场费 - 竞拍出价
            return this.landlordRevenue - this.entryFee - this.bidAmount;
        } else {
            // 农民收益 = 手牌价值 - 入场费
            return this.getHandValue() - this.entryFee;
        }
    }

    reset() {
        this.handCards = [];
        this.drawnCards.clear();
        this.currentRoundCards = [];
        this.isActive = true;
        this.roundCount = 0;
        this.bidAmount = 0;
        this.role = 'farmer';
        this.landlordRevenue = 0;
    }
}

class GameEngine {
    constructor() {
        this.players = [];
        this.cardDeck = [];
        this.gameState = 'waiting'; // 'waiting' | 'bidding' | 'playing' | 'finished'
        this.currentPlayerIndex = 0;
        this.biddingRound = 0;
        this.currentBid = 0;
        this.currentBidder = null;
        this.landlord = null;
        this.totalPool = 400; // 基础奖池
        this.gameRound = 0; // 游戏回合数
        this.roundPhase = 'draw'; // 'draw' | 'flip' | 'decide'
        this.playersDrawnThisRound = new Set(); // 本轮已抽牌的玩家
        this.playersActedThisRound = new Set(); // 本轮已行动的玩家ID
        this.biddingTurnCount = 0; // 竞价次数计数器
    }

    // 初始化游戏
    initializeGame(playerNames = ['玩家A', '玩家B', '玩家C', '玩家D']) {
        this.players = playerNames.map(name => new Player(uuidv4(), name));
        this.gameState = 'bidding';
        this.currentPlayerIndex = 0;
        this.biddingRound = 0;
        this.currentBid = 0;
        this.currentBidder = null;
        this.biddingTurnCount = 0; // 竞价次数计数器
        this.landlord = null;
        this.totalPool = 400;

        this.generateCardDeck();
        return this.getGameState();
    }

    // 生成牌库
    generateCardDeck() {
        this.cardDeck = [];

        // 每个玩家贡献5张牌到牌库
        this.players.forEach((player, index) => {
            for (let i = 0; i < 5; i++) {
                const card = new Card(
                    uuidv4(),
                    'value',
                    Math.floor(Math.random() * 50) + 10, // 10-60的随机价值
                    player.id
                );
                this.cardDeck.push(card);
            }
        });

        // 重新分配价值以确保零和
        this.redistributeValues();
    }

    // 重新分配价值确保零和平衡
    redistributeValues() {
        const hasLandlord = this.landlord !== null;
        let totalValue = this.totalPool + (hasLandlord ? this.currentBid : 0);

        if (hasLandlord) {
            // 有地主模式：15张价值牌(300) + 5张地主炸弹牌 + 5张系统价值牌(100+出价)
            const playerValueCards = this.cardDeck.filter(card =>
                card.originalOwner !== this.landlord.id
            ).slice(0, 15);

            const landlordCards = this.cardDeck.filter(card =>
                card.originalOwner === this.landlord.id
            );

            // 地主的牌转为炸弹牌
            landlordCards.forEach(card => {
                card.type = 'bomb';
                card.originalValue = 0;
                card.currentValue = 0;
            });

            // 分配300积分给15张玩家价值牌
            this.distributeValues(playerValueCards, 300);

            // 添加5张系统价值牌
            for (let i = 0; i < 5; i++) {
                const systemCard = new Card(
                    uuidv4(),
                    'system_value',
                    (100 + this.currentBid) / 5,
                    'system'
                );
                this.cardDeck.push(systemCard);
            }
        } else {
            // 无地主模式：20张价值牌(400) + 5张系统炸弹牌
            const valueCards = this.cardDeck.slice(0, 20);
            this.distributeValues(valueCards, 400);

            // 添加5张系统炸弹牌
            for (let i = 0; i < 5; i++) {
                const bombCard = new Card(uuidv4(), 'system_bomb', 0, 'system');
                this.cardDeck.push(bombCard);
            }
        }

        // 打乱牌库
        this.shuffleDeck();
    }

    // 分配价值给指定牌组
    distributeValues(cards, totalValue) {
        const values = [];
        let remaining = totalValue;

        for (let i = 0; i < cards.length - 1; i++) {
            const value = Math.floor(Math.random() * (remaining / 2)) + 1;
            values.push(value);
            remaining -= value;
        }
        values.push(remaining);

        // 打乱价值分配
        for (let i = values.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [values[i], values[j]] = [values[j], values[i]];
        }

        cards.forEach((card, index) => {
            card.originalValue = values[index];
            card.currentValue = values[index];
        });
    }

    // 打乱牌库
    shuffleDeck() {
        for (let i = this.cardDeck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [this.cardDeck[i], this.cardDeck[j]] = [this.cardDeck[j], this.cardDeck[i]];
        }
    }

    // 竞拍出价
    placeBid(playerId, amount) {
        if (this.gameState !== 'bidding') {
            return { success: false, message: '当前不在竞拍阶段' };
        }

        const player = this.players[this.currentPlayerIndex];
        if (player.id !== playerId) {
            return { success: false, message: '不是当前竞拍玩家' };
        }

        if (amount > 0 && amount <= this.currentBid) {
            return { success: false, message: '出价必须高于当前最高价' };
        }

        if (amount > 0) {
            this.currentBid = amount;
            this.currentBidder = player;
            player.bidAmount = amount;
        }

        // 增加竞价次数
        this.biddingTurnCount++;

        // 检查是否完成5次竞价
        if (this.biddingTurnCount >= 5) {
            this.endBidding();
        } else {
            this.nextBiddingPlayer();
        }

        return { success: true, gameState: this.getGameState() };
    }

    // 下一个竞拍玩家
    nextBiddingPlayer() {
        this.currentPlayerIndex = (this.currentPlayerIndex + 1) % this.players.length;
    }

    // 结束竞拍
    endBidding() {
        if (this.currentBidder) {
            this.landlord = this.currentBidder;
            this.landlord.role = 'landlord';
            this.totalPool += this.currentBid;
        }

        this.regenerateCardDeckAfterBidding();
        this.gameState = 'playing';
        this.gameRound = 1;
        this.roundPhase = 'draw';
        this.playersDrawnThisRound = new Set();
        this.playersActedThisRound = new Set();
        // 注意：drawnCardsThisRound 已被移除，不再需要清空
        this.currentPlayerIndex = 0;

        // 跳过地主，从第一个农民开始
        while (this.players[this.currentPlayerIndex].role === 'landlord') {
            this.currentPlayerIndex = (this.currentPlayerIndex + 1) % this.players.length;
        }
    }

    // 竞拍结束后重新生成牌库
    regenerateCardDeckAfterBidding() {
        this.cardDeck = [];
        this.generateCardDeck();
    }

    // 农民抽牌
    drawCards(playerId) {
        if (this.gameState !== 'playing') {
            return { success: false, message: '当前不在游戏阶段' };
        }

        if (this.roundPhase !== 'draw') {
            return { success: false, message: '当前不在抽牌阶段' };
        }

        const player = this.players.find(p => p.id === playerId);
        if (!player || player.role === 'landlord' || !player.isActive) {
            return { success: false, message: '玩家状态错误' };
        }

        if (this.playersDrawnThisRound.has(playerId)) {
            return { success: false, message: '本轮已抽过牌' };
        }

        // 每次抽牌时都重新计算可用牌池，排除所有玩家历史抽过的牌
        const availableCards = this.cardDeck.filter(card => {
            return !this.players.some(p => p.drawnCards.has(card.id));
        });

        if (availableCards.length < 5) {
            return { success: false, message: '可抽牌数量不足' };
        }

        // 从可用牌池中随机抽取5张
        const shuffled = [...availableCards].sort(() => Math.random() - 0.5);
        const drawnCards = shuffled.slice(0, 5);

        // 记录玩家抽过的牌（防重复）
        drawnCards.forEach(card => {
            player.drawnCards.add(card.id);
        });

        // 记录玩家本轮抽到的牌
        player.currentRoundCards = drawnCards.map(card => card.id);
        this.playersDrawnThisRound.add(playerId);

        // 检查是否所有农民都已抽牌
        const activeFarmers = this.players.filter(p => p.role === 'farmer' && p.isActive);
        if (this.playersDrawnThisRound.size === activeFarmers.length) {
            this.roundPhase = 'flip';
        }

        return {
            success: true,
            cards: drawnCards.map(card => ({
                id: card.id,
                type: 'hidden'
            })),
            gameState: this.getGameState()
        };
    }

    // 翻牌
    flipCards(playerId, cardIds) {
        if (this.gameState !== 'playing') {
            return { success: false, message: '当前不在游戏阶段' };
        }

        if (this.roundPhase !== 'flip') {
            return { success: false, message: '当前不在翻牌阶段' };
        }

        const player = this.players.find(p => p.id === playerId);
        if (!player || player.role === 'landlord' || !player.isActive) {
            return { success: false, message: '玩家状态错误' };
        }

        if (!player.currentRoundCards || player.currentRoundCards.length === 0) {
            return { success: false, message: '玩家本轮未抽牌' };
        }

        if (cardIds.length === 0) {
            return { success: false, message: '至少需要翻开一张牌' };
        }

        // 验证翻牌的卡片是否为玩家本轮抽到的
        for (const cardId of cardIds) {
            if (!player.currentRoundCards.includes(cardId)) {
                return { success: false, message: '只能翻开本轮抽到的牌' };
            }
        }

        const results = [];
        let triggeredBomb = false;

        for (const cardId of cardIds) {
            const card = this.cardDeck.find(c => c.id === cardId);
            if (!card) continue;

            const result = {
                id: cardId,
                type: card.type,
                value: card.flip()
            };
            results.push(result);

            if (card.type === 'bomb' || card.type === 'system_bomb') {
                triggeredBomb = true;
                break;
            } else if (card.type === 'value' || card.type === 'system_value') {
                player.addCardToHand(card);
            }
        }

        if (triggeredBomb) {
            player.isActive = false;
        }

        // 从本轮抽牌记录中移除已翻开的牌
        cardIds.forEach(cardId => {
            const index = player.currentRoundCards.indexOf(cardId);
            if (index > -1) {
                player.currentRoundCards.splice(index, 1);
            }
        });

        // 如果触发炸弹或玩家选择结束，才完成行动
        if (triggeredBomb) {
            // 炸弹触发：还回所有剩余牌，玩家离场
            this.returnCardsTodeck(player.currentRoundCards);
            player.currentRoundCards = [];
            player.roundCount++;
            this.playersActedThisRound.add(playerId);

            // 检查游戏是否结束
            const activeFarmers = this.players.filter(p => p.role === 'farmer' && p.isActive);
            if (activeFarmers.length === 0) {
                this.endGame();
            } else {
                // 检查所有已抽牌的玩家是否都已行动
                if (this.playersActedThisRound.size === this.playersDrawnThisRound.size) {
                    this.nextRound();
                }
            }
        }
        // 如果没有触发炸弹，玩家可以继续翻牌或选择离场

        return {
            success: true,
            results: results,
            triggeredBomb: triggeredBomb,
            gameState: this.getGameState()
        };
    }

    // 玩家主动离场（结束本轮行动）
    leaveGame(playerId) {
        const player = this.players.find(p => p.id === playerId);
        if (!player || !player.isActive) {
            return { success: false, message: '玩家状态错误' };
        }

        player.isActive = false;

        // 还牌：将本轮抽到的所有牌放回牌库（重置翻牌状态）
        this.returnCardsTodeck(player.currentRoundCards);

        player.currentRoundCards = []; // 清空本轮抽牌记录
        player.roundCount++;
        this.playersActedThisRound.add(playerId);

        // 检查是否所有已抽牌的玩家都已行动或游戏结束
        const activeFarmers = this.players.filter(p => p.role === 'farmer' && p.isActive);
        if (activeFarmers.length === 0) {
            this.endGame();
        } else if (this.playersActedThisRound.size === this.playersDrawnThisRound.size) {
            this.nextRound();
        }

        return { success: true, gameState: this.getGameState() };
    }

    // 玩家结束翻牌（主动结束本轮行动）
    endFlipping(playerId) {
        const player = this.players.find(p => p.id === playerId);
        if (!player || !player.isActive || player.role === 'landlord') {
            return { success: false, message: '玩家状态错误' };
        }

        // 还牌：将剩余未翻开的牌放回牌库
        this.returnCardsTodeck(player.currentRoundCards);

        player.currentRoundCards = [];
        player.roundCount++;
        this.playersActedThisRound.add(playerId);

        // 检查所有已抽牌的玩家是否都已行动
        if (this.playersActedThisRound.size === this.playersDrawnThisRound.size) {
            this.nextRound();
        }

        return { success: true, gameState: this.getGameState() };
    }

    // 还牌方法：将指定牌放回牌库
    returnCardsTodeck(cardIds) {
        if (!cardIds || cardIds.length === 0) return;

        cardIds.forEach(cardId => {
            const card = this.cardDeck.find(c => c.id === cardId);
            if (card) {
                card.resetFlipState(); // 重置翻牌状态，让牌可以重新被抽取
            }
        });
    }

    // 下一轮游戏
    nextRound() {
        if (this.checkGameEnd()) {
            this.endGame();
            return;
        }

        // 检查是否达到最大回合数
        if (this.gameRound >= 5) {
            this.endGame();
            return;
        }

        this.gameRound++;
        this.roundPhase = 'draw';
        this.playersDrawnThisRound.clear();
        this.playersActedThisRound.clear();

        // 清空所有玩家的本轮抽牌记录
        this.players.forEach(player => {
            if (player.currentRoundCards) {
                player.currentRoundCards = [];
            }
        });
    }

    // 检查游戏结束
    checkGameEnd() {
        const activeFarmers = this.players.filter(p => p.role === 'farmer' && p.isActive);
        return activeFarmers.length === 0;
    }

    // 结束游戏
    endGame() {
        this.gameState = 'finished';

        // 计算地主收益
        if (this.landlord) {
            const remainingValue = this.cardDeck.reduce((total, card) => {
                return total + card.currentValue;
            }, 0);
            this.landlord.landlordRevenue = remainingValue;
        }
    }

    // 获取当前玩家
    getCurrentPlayer() {
        if (this.gameState === 'bidding') {
            return this.players[this.currentPlayerIndex];
        } else if (this.gameState === 'playing') {
            // 在游戏阶段，所有农民都可以行动
            return null; // 不再有单一当前玩家概念
        }
        return null;
    }

    // 获取游戏状态
    getGameState() {
        const valueCards = this.cardDeck.filter(card =>
            (card.type === 'value' || card.type === 'system_value') && card.currentValue > 0
        );

        return {
            gameState: this.gameState,
            gameRound: this.gameRound,
            roundPhase: this.roundPhase,
            currentPlayerIndex: this.currentPlayerIndex,
            playersDrawnThisRound: Array.from(this.playersDrawnThisRound),
            playersActedThisRound: Array.from(this.playersActedThisRound),
            players: this.players.map(p => ({
                id: p.id,
                name: p.name,
                role: p.role,
                isActive: p.isActive,
                handValue: p.getHandValue(),
                handCount: p.handCards.length,
                roundCount: p.roundCount,
                bidAmount: p.bidAmount,
                entryFee: p.entryFee,
                finalScore: this.gameState === 'finished' ? p.getFinalScore() : null,
                hasDrawnThisRound: this.playersDrawnThisRound.has(p.id),
                hasActedThisRound: this.playersActedThisRound.has(p.id),
                currentRoundCards: p.currentRoundCards || []
            })),
            biddingInfo: {
                currentBid: this.currentBid,
                currentBidder: this.currentBidder?.name,
                biddingRound: this.biddingRound,
                biddingTurnCount: this.biddingTurnCount
            },
            landlord: this.landlord?.name,
            totalPool: this.totalPool,
            deckInfo: {
                totalCards: this.cardDeck.length,
                remainingValue: this.cardDeck.reduce((total, card) => total + card.currentValue, 0),
                flippedCards: this.cardDeck.filter(card => card.isFlipped).length,
                remainingValueCards: valueCards.length,
                remainingValueTotal: valueCards.reduce((total, card) => total + card.currentValue, 0)
            }
        };
    }

    // 重置游戏
    resetGame() {
        this.players.forEach(player => player.reset());
        this.cardDeck = [];
        this.gameState = 'waiting';
        this.currentPlayerIndex = 0;
        this.biddingRound = 0;
        this.currentBid = 0;
        this.currentBidder = null;
        this.biddingTurnCount = 0;
        this.landlord = null;
        this.totalPool = 400;
        this.gameRound = 0;
        this.roundPhase = 'draw';
        this.playersDrawnThisRound = new Set();
        this.playersActedThisRound = new Set();
        this.drawnCardsThisRound = new Set();
    }

    // 调试功能：调整玩家外部数值
    adjustPlayerValues(playerId, adjustments) {
        const player = this.players.find(p => p.id === playerId);
        if (!player) return { success: false, message: '玩家不存在' };

        if (adjustments.entryFee !== undefined) {
            player.entryFee = adjustments.entryFee;
        }

        return { success: true, player: player };
    }

    // 调试功能：手动设置牌库
    setCardDeck(cards) {
        this.cardDeck = cards.map(cardData => {
            const card = new Card(cardData.id || uuidv4(), cardData.type, cardData.value);
            if (cardData.isFlipped) {
                card.flip();
            }
            return card;
        });
        return { success: true };
    }
}

module.exports = { GameEngine, Player, Card };
