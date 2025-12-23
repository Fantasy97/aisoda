const socket = io();
let gameState = {};
let currentPlayerId = null;
let drawnCards = [];
let selectedCards = new Set();

// Socket事件监听
socket.on('gameStateUpdate', (state) => {
    gameState = state;
    updateUI();
    logMessage(`游戏状态更新: ${state.gameState} - 第${state.gameRound}轮 - ${getRoundPhaseText(state.roundPhase)}`, 'info');
    updateDebugPanel(); // 更新调试面板
});

// 监听所有Socket.IO事件用于调试
socket.onAny((eventName, ...args) => {
    logSocketEvent(eventName, args);
});

socket.on('cardsDrawn', (data) => {
    logMessage(`${getPlayerName(data.playerId)} 抽取了 ${data.cards.length} 张牌`, 'info');
    // 更新整个抽牌区域显示
    setTimeout(() => updatePlayersCardsDisplay(), 100);
});

socket.on('cardsFlipped', (data) => {
    if (data.triggeredBomb) {
        logMessage(`${getPlayerName(data.playerId)} 触发炸弹离场!`, 'error');
    } else {
        logMessage(`${getPlayerName(data.playerId)} 翻开了 ${data.results.length} 张牌`, 'success');
        // 显示翻牌详细信息
        data.results.forEach(result => {
            logMessage(`  - 卡片 ${result.id.substring(0, 8)}: ${getCardTypeText(result.type)}, 价值: ${result.value}, 原主人: ${getPlayerName(result.originalOwner)}`, 'info');
        });
    }
    
    // 关闭翻牌面板
    closeFlipPanel();
    
    // 更新整个抽牌区域显示
    setTimeout(() => updatePlayersCardsDisplay(), 100);
});

socket.on('playerLeft', (data) => {
    logMessage(`${getPlayerName(data.playerId)} 主动离场`, 'warning');
});

// 初始化游戏
function initGame() {
    const playerNames = ['玩家A', '玩家B', '玩家C', '玩家D'];
    fetch('/api/init-game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playerNames })
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              logMessage('游戏初始化成功', 'success');
          }
      });
}

// 重置游戏
function resetGame() {
    fetch('/api/reset-game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              drawnCards = [];
              selectedCards.clear();
              logMessage('游戏已重置', 'info');
          }
      });
}

// 竞拍出价
function placeBid() {
    const amount = parseInt(document.getElementById('bidAmount').value) || 0;
    const currentPlayer = getCurrentPlayer();
    if (!currentPlayer) return;

    fetch('/api/place-bid', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playerId: currentPlayer.id, amount })
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              document.getElementById('bidAmount').value = '';
              logMessage(`${currentPlayer.name} 出价 ${amount} 积分`, 'info');
          } else {
              logMessage(`出价失败: ${data.message}`, 'error');
          }
      });
}

// 放弃竞拍
function passBid() {
    const currentPlayer = getCurrentPlayer();
    if (!currentPlayer) return;

    fetch('/api/place-bid', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playerId: currentPlayer.id, amount: 0 })
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              logMessage(`${currentPlayer.name} 放弃竞拍`, 'warning');
          }
      });
}

// 抽牌
function drawCardsForPlayer(playerId) {
    fetch('/api/draw-cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playerId: playerId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            logMessage(`${getPlayerName(playerId)} 抽取了 ${data.cards.length} 张牌`, 'success');
        } else {
            logMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('抽牌失败:', error);
        logMessage('抽牌失败', 'error');
    });
}

function drawCards() {
    if (!currentPlayerId) {
        logMessage('请先选择玩家', 'error');
        return;
    }
    drawCardsForPlayer(currentPlayerId);
}

// 翻牌
function flipSelectedCards() {
    if (selectedCards.size === 0) {
        logMessage('请至少选择一张牌', 'warning');
        return;
    }

    const currentPlayer = getCurrentPlayer();
    if (!currentPlayer) return;

    const cardIds = Array.from(selectedCards);
    fetch('/api/flip-cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playerId: currentPlayer.id, cardIds })
    }).then(response => response.json())
      .then(data => {
          if (!data.success) {
              logMessage(`翻牌失败: ${data.message}`, 'error');
          } else {
              selectedCards.clear();
          }
      });
}

// 离场
function leaveGame() {
    const currentPlayer = getCurrentPlayer();
    if (!currentPlayer) return;

    if (confirm(`确定要让 ${currentPlayer.name} 离场吗？`)) {
        fetch('/api/leave-game', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ playerId: currentPlayer.id })
        }).then(response => response.json())
          .then(data => {
              if (!data.success) {
                  logMessage(`离场失败: ${data.message}`, 'error');
              }
          });
    }
}

// 切换调试面板
function toggleDebug() {
    const debugSection = document.getElementById('debugSection');
    debugSection.style.display = debugSection.style.display === 'none' ? 'block' : 'none';
}

// 调试面板函数
function updateDebugPanel() {
    const gameStateDebugEl = document.getElementById('gameStateDebug');
    if (gameStateDebugEl) {
        gameStateDebugEl.textContent = JSON.stringify(gameState, null, 2);
    }
}

function copyGameStateToClipboard() {
    const stateText = JSON.stringify(gameState, null, 2);
    navigator.clipboard.writeText(stateText).then(() => {
        logMessage('游戏状态已复制到剪贴板', 'success');
    }).catch(err => {
        logMessage('复制失败', 'error');
        console.error('无法复制状态: ', err);
    });
}

function logSocketEvent(eventName, args) {
    const socketLogEl = document.getElementById('socketEventsLog');
    if (!socketLogEl) return;

    const entry = document.createElement('div');
    entry.className = 'socket-log-entry';

    const eventEl = document.createElement('div');
    eventEl.className = 'socket-log-event';
    eventEl.textContent = `[${new Date().toLocaleTimeString()}] ${eventName}`;

    const dataEl = document.createElement('div');
    dataEl.className = 'socket-log-data';
    dataEl.textContent = JSON.stringify(args, null, 2);

    entry.appendChild(eventEl);
    entry.appendChild(dataEl);

    socketLogEl.appendChild(entry);
    socketLogEl.scrollTop = socketLogEl.scrollHeight; // 自动滚动到底部
}



// 清空日志
function clearLogs() {
    document.getElementById('gameLog').innerHTML = '';
    const socketLogEl = document.getElementById('socketEventsLog');
    if (socketLogEl) {
        socketLogEl.innerHTML = '';
    }
}

// UI更新函数
function updateUI() {
    updateGameInfo();
    updatePlayersDisplay();
    updateBiddingSection();
    updateCardsSection();
}

function updateGameInfo() {
    document.getElementById('gameState').textContent = getGameStateText();
    document.getElementById('totalPool').textContent = gameState.totalPool || 0;
    document.getElementById('currentBid').textContent = gameState.biddingInfo?.currentBid || 0;
    document.getElementById('totalCards').textContent = gameState.deckInfo?.totalCards || 0;
    document.getElementById('remainingValue').textContent = gameState.deckInfo?.remainingValue || 0;
    
    // 更新回合信息
    if (gameState.gameState === 'playing') {
        document.getElementById('gameRound').textContent = gameState.gameRound || 0;
        document.getElementById('roundPhase').textContent = getRoundPhaseText(gameState.roundPhase);
        document.getElementById('remainingValueCards').textContent = gameState.deckInfo?.remainingValueCards || 0;
        document.getElementById('remainingValueTotal').textContent = gameState.deckInfo?.remainingValueTotal || 0;
    }
}

function updatePlayersDisplay() {
    const container = document.getElementById('playersGrid');
    if (!container || !gameState.players) return;

    container.innerHTML = '';
    
    gameState.players.forEach(player => {
        // 更新玩家状态：检查是否已抽牌和已行动
        player.hasDrawnThisRound = gameState.playersDrawnThisRound?.includes(player.id) || false;
        player.hasActedThisRound = gameState.playersActedThisRound?.includes(player.id) || false;
        
        const section = createPlayerCard(player);
        container.appendChild(section);
    });
}

function createPlayerCard(player) {
    const card = document.createElement('div');
    let cardClass = `player-card ${player.isActive ? 'active' : 'inactive'} ${player.role === 'landlord' ? 'landlord' : ''}`;
    
    // 检查是否为当前选中的玩家
    const isCurrentPlayer = currentPlayerId === player.id;
    
    // 在游戏阶段，高亮显示可以行动的农民
    if (gameState.gameState === 'playing' && player.role === 'farmer' && player.isActive) {
        if (gameState.roundPhase === 'draw' && !player.hasDrawnThisRound) {
            cardClass += ' can-draw';
        } else if (gameState.roundPhase === 'flip' && player.hasDrawnThisRound && !player.hasActedThisRound) {
            cardClass += ' can-flip';
        }
    }
    
    // 如果是当前选中的玩家，添加特殊样式
    if (isCurrentPlayer) {
        cardClass += ' selected-player';
    }
    
    card.className = cardClass;

    card.innerHTML = `
        <div class="player-header">
            <span class="player-name">${player.name} ${isCurrentPlayer ? '(当前)' : ''}</span>
            <span class="player-role role-${player.role}">${player.role === 'landlord' ? '地主' : '农民'}</span>
        </div>
        <div class="player-stats">
            <div class="stat">
                <div class="stat-label">手牌价值</div>
                <div class="stat-value">${player.handValue}</div>
            </div>
            <div class="stat">
                <div class="stat-label">手牌数量</div>
                <div class="stat-value">${player.handCount}</div>
            </div>
            <div class="stat">
                <div class="stat-label">回合数</div>
                <div class="stat-value">${player.roundCount}/5</div>
            </div>
            <div class="stat">
                <div class="stat-label">最终积分</div>
                <div class="stat-value">${player.finalScore !== null ? player.finalScore : '-'}</div>
            </div>
        </div>
        <div class="player-actions">
            <button class="btn btn-primary" onclick="setCurrentPlayer('${player.id}')" 
                    ${!player.isActive ? 'disabled' : ''}>
                选择操控
            </button>
            ${getPlayerActionButtons(player)}
        </div>
    `;

    return card;
}

function updateBiddingSection() {
    const section = document.getElementById('biddingSection');
    const isVisible = gameState.gameState === 'bidding';
    section.style.display = isVisible ? 'block' : 'none';

    if (isVisible) {
        document.getElementById('biddingCurrentBid').textContent = gameState.biddingInfo?.currentBid || 0;
        document.getElementById('currentBidder').textContent = gameState.biddingInfo?.currentBidder || '无';
        
        // 显示当前轮到的竞拍玩家
        const currentBiddingPlayer = getCurrentBiddingPlayer();
        const biddingInfo = document.querySelector('.bidding-info');
        if (currentBiddingPlayer && biddingInfo) {
            const existingCurrentPlayer = biddingInfo.querySelector('.current-bidding-player');
            if (existingCurrentPlayer) {
                existingCurrentPlayer.remove();
            }
            
            const currentPlayerDiv = document.createElement('div');
            currentPlayerDiv.className = 'current-bidding-player';
            currentPlayerDiv.innerHTML = `<strong>当前轮到：${currentBiddingPlayer.name}</strong>`;
            biddingInfo.appendChild(currentPlayerDiv);
        }
    }
}

function updateCardsSection() {
    const section = document.getElementById('cardsSection');
    const roundInfo = document.getElementById('roundInfo');
    const isVisible = gameState.gameState === 'playing';
    section.style.display = isVisible ? 'block' : 'none';
    roundInfo.style.display = isVisible ? 'block' : 'none';

    if (isVisible) {
        updatePlayersCardsDisplay();
    }
}

function updatePlayersCardsDisplay() {
    const container = document.getElementById('playersCardsContainer');
    if (!container) {
        console.error('playersCardsContainer not found');
        return;
    }
    
    container.innerHTML = '';

    if (!gameState.players) {
        console.warn('No players in gameState');
        return;
    }

    console.log('Updating cards display for players:', gameState.players.map(p => p.name));
    
    gameState.players.forEach(player => {
        if (player.role === 'landlord') return; // 地主不显示抽牌区域
        
        const playerSection = createPlayerCardsSection(player);
        container.appendChild(playerSection);
        
        console.log(`Created section for player ${player.name} (${player.id})`);
    });
}

function createPlayerCardsSection(player) {
    const section = document.createElement('div');
    section.className = `player-cards-section ${player.isActive ? 'active' : 'inactive'} ${player.role === 'landlord' ? 'landlord' : ''}`;
    section.id = `player-cards-${player.id}`;
    
    // 获取玩家的抽牌状态
    const hasDrawn = gameState.playersDrawnThisRound?.includes(player.id) || false;
    const hasActed = gameState.playersActedThisRound?.includes(player.id) || false;
    
    section.innerHTML = `
        <div class="player-cards-header">
            <div class="player-name">${player.name}</div>
            <div class="player-status ${hasDrawn ? 'drawn' : ''} ${hasActed ? 'acted' : ''}">
                ${hasActed ? '已行动' : hasDrawn ? '已抽牌' : '待抽牌'}
            </div>
        </div>
        <div class="player-cards-grid" id="cards-${player.id}"></div>
        <div class="player-actions">
            ${getPlayerCardActions(player, hasDrawn, hasActed)}
        </div>
    `;
    
    // 如果玩家已抽牌，加载其手牌
    if (hasDrawn) {
        setTimeout(() => loadPlayerCards(player.id), 50);
    }
    
    return section;
}

function getPlayerCardActions(player, hasDrawn, hasActed) {
    if (!player.isActive) return '<span class="text-muted">已离场</span>';
    
    let buttons = '';
    
    if (gameState.roundPhase === 'draw' && !hasDrawn) {
        buttons += `<button class="btn btn-primary btn-sm" onclick="drawCardsForPlayer('${player.id}')">抽牌</button>`;
    }
    
    if (gameState.roundPhase === 'flip' && hasDrawn && !hasActed) {
        buttons += `<button class="btn btn-warning btn-sm" onclick="flipSelectedCardsForPlayer('${player.id}')">翻牌</button>`;
        buttons += `<button class="btn btn-danger btn-sm" onclick="leaveGameForPlayer('${player.id}')">离场</button>`;
    }
    
    return buttons || '<span class="text-muted">等待中</span>';
}

function loadPlayerCards(playerId) {
    console.log(`Loading cards for player: ${playerId}`);
    fetch(`/api/player-cards/${playerId}`)
        .then(response => response.json())
        .then(data => {
            console.log(`Cards loaded for ${playerId}:`, data);
            if (data.success) {
                displayPlayerCards(playerId, data.cards);
            } else {
                console.warn(`Failed to load cards for ${playerId}:`, data.message);
            }
        })
        .catch(error => {
            console.error('Failed to load player cards:', error);
        });
}

function displayPlayerCards(playerId, cards) {
    console.log(`Displaying cards for player ${playerId}:`, cards);
    const container = document.getElementById(`cards-${playerId}`);
    if (!container) {
        console.error(`Container cards-${playerId} not found`);
        return;
    }
    
    container.innerHTML = '';
    
    cards.forEach(card => {
        const cardElement = createCardElement(card, playerId);
        cardElement.id = `card-dom-${card.id}`; // 为卡牌元素添加唯一ID
        container.appendChild(cardElement);
        console.log(`Added card ${card.id} to player ${playerId} container`);
    });
    
    // 添加翻牌操作区域
    const player = gameState.players?.find(p => p.id === playerId);
    const hasDrawn = gameState.playersDrawnThisRound?.includes(playerId) || false;
    const hasActed = gameState.playersActedThisRound?.includes(playerId) || false;
    
    if (gameState.roundPhase === 'flip' && hasDrawn && !hasActed) {
        const flipInfo = document.createElement('div');
        flipInfo.className = 'flip-operation-info';
        flipInfo.innerHTML = `
            <p>点击卡牌逐张翻开，剩余: <span id="remaining-count-${playerId}">${cards.filter(c => c.type === 'hidden').length}</span> 张未翻开</p>
            <button class="btn btn-success btn-sm" onclick="endFlippingForPlayer('${playerId}')">结束翻牌</button>
            <button class="btn btn-danger btn-sm" onclick="leaveGameForPlayer('${playerId}')">离场</button>
        `;
        container.appendChild(flipInfo);
    }
    
    // 翻牌结果显示区域 - 确保每次都重新创建
    let resultsContainer = document.getElementById(`flip-results-${playerId}`);
    if (resultsContainer) {
        resultsContainer.remove(); // 移除旧的容器
    }
    
    resultsContainer = document.createElement('div');
    resultsContainer.id = `flip-results-${playerId}`;
    resultsContainer.className = 'flip-results';
    resultsContainer.style.cssText = 'min-height: 40px; margin-top: 10px; padding: 5px; border: 1px dashed #ccc; background: #f9f9f9;';
    container.appendChild(resultsContainer);
    console.log(`Created flip results container for player ${playerId}`);
}

function createCardElement(card, playerId) {
    const element = document.createElement('div');
    element.className = `card ${card.type || 'hidden'}`;
    
    // 抽牌后直接点击卡牌即可翻开
    const hasDrawn = gameState.playersDrawnThisRound?.includes(playerId) || false;
    const hasActed = gameState.playersActedThisRound?.includes(playerId) || false;
    
    if (hasDrawn && !hasActed && card.type === 'hidden') {
        element.onclick = () => flipSingleCard(card.id, playerId);
        element.style.cursor = 'pointer';
        element.title = '点击翻开此牌';
    }

    if (card.type === 'hidden') {
        element.innerHTML = '<div class="card-value">?</div>';
    } else {
        // 显示翻开后的卡牌详细信息
        const typeClass = card.type === 'bomb' || card.type === 'system_bomb' ? 'bomb-card' : 'value-card';
        element.classList.add(typeClass);
        
        const typeIcon = card.type === 'bomb' || card.type === 'system_bomb' ? '💣' : '💎';
        const valueDisplay = card.value > 0 ? `+${card.value}` : '0';
        
        element.innerHTML = `
            <div class="card-icon">${typeIcon}</div>
            <div class="card-type">${getCardTypeText(card.type)}</div>
            <div class="card-value">${valueDisplay}</div>
            <div class="card-info">ID: ${card.id.substring(0, 8)}</div>
        `;
        
        // 禁用点击
        element.style.cursor = 'default';
        element.onclick = null;
    }

    return element;
}

// 新增单张翻牌功能
function flipSingleCard(cardId, playerId) {
    console.log(`Flipping card ${cardId} for player ${playerId}`);
    fetch('/api/flip-cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            playerId: playerId,
            cardIds: [cardId]
        })
    }).then(response => response.json())
      .then(data => {
          console.log('Flip response:', data);
          if (!data.success) {
              logMessage(`翻牌失败: ${data.message}`, 'error');
          } else {
              // 显示翻牌结果
              if (data.results && data.results.length > 0) {
                  const result = data.results[0];
                  const typeText = getCardTypeText(result.type);
                  const valueText = result.value > 0 ? `+${result.value}` : '0';
                  
                  if (result.type === 'bomb' || result.type === 'system_bomb') {
                      logMessage(`💣 ${getPlayerName(playerId)} 翻到炸弹！玩家离场`, 'error');
                  } else {
                      logMessage(`💎 ${getPlayerName(playerId)} 翻到${typeText}，价值: ${valueText}`, 'success');
                  }
                  
                  // 更新卡牌DOM以显示翻牌结果
                  updateFlippedCardDOM(cardId, result);
              }
              
              // 更新显示 - 直接更新DOM，不再重新加载
              updateRemainingCardCount(playerId);
              // 轻微延迟以确保DOM更新后获取最新游戏状态
              setTimeout(() => updateGameState(), 100);
          }
      })
      .catch(error => {
          logMessage(`翻牌请求失败: ${error.message}`, 'error');
      });
}

// 结束翻牌操作
function endFlippingForPlayer(playerId) {
    console.log(`Ending flipping for player: ${playerId}`);
    fetch('/api/end-flipping', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playerId })
    }).then(response => response.json())
      .then(data => {
          console.log('End flipping response:', data);
          if (!data.success) {
              logMessage(`结束翻牌失败: ${data.message}`, 'error');
          } else {
              logMessage(`${getPlayerName(playerId)} 结束翻牌`, 'info');
              setTimeout(() => updatePlayersCardsDisplay(), 100);
          }
      })
      .catch(error => {
          logMessage(`结束翻牌请求失败: ${error.message}`, 'error');
      });
}

// 更新剩余卡牌计数
function updateRemainingCardCount(playerId) {
    const countElement = document.getElementById(`remaining-count-${playerId}`);
    if (countElement) {
        fetch(`/api/player-cards/${playerId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const hiddenCount = data.cards.filter(c => c.type === 'hidden').length;
                    countElement.textContent = hiddenCount;
                }
            });
    }
}

// 在玩家区域显示翻牌结果提示
function showFlipResultInPlayerArea(playerId, result) {
    console.log(`=== FLIP RESULT DEBUG === Player: ${playerId}, Result:`, result);
    
    // 查找翻牌结果容器
    const resultsContainer = document.getElementById(`flip-results-${playerId}`);
    console.log(`Results container for ${playerId}:`, resultsContainer);
    
    if (!resultsContainer) {
        console.error(`❌ Results container flip-results-${playerId} not found`);
        // 直接在玩家卡牌容器中显示
        const cardsContainer = document.getElementById(`cards-${playerId}`);
        console.log(`Fallback: cards container for ${playerId}:`, cardsContainer);
        if (cardsContainer) {
            showFlipResultInContainer(cardsContainer, result, playerId);
        }
        return;
    }
    
    // 清空之前的结果
    resultsContainer.innerHTML = '';
    
    const typeIcon = result.type === 'bomb' || result.type === 'system_bomb' ? '💣' : '💎';
    const valueText = result.value > 0 ? `+${result.value}` : '0';
    
    const resultElement = document.createElement('div');
    resultElement.style.cssText = `
        background: ${result.type === 'bomb' || result.type === 'system_bomb' ? '#f8d7da' : '#d4edda'};
        border: 2px solid ${result.type === 'bomb' || result.type === 'system_bomb' ? '#dc3545' : '#28a745'};
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        text-align: center;
        font-weight: bold;
        animation: fadeIn 0.5s ease-in;
    `;
    
    resultElement.innerHTML = `
        ${typeIcon} 翻牌结果: ${getCardTypeText(result.type)} 价值: ${valueText}
    `;
    
    resultsContainer.appendChild(resultElement);
    console.log(`✅ Added flip result to player ${playerId} results container`);
    
    // 10秒后自动移除提示
    setTimeout(() => {
        if (resultElement.parentNode) {
            resultElement.remove();
            console.log(`Removed flip result for player ${playerId}`);
        }
    }, 10000);
}

// 在指定容器中显示翻牌结果
function showFlipResultInContainer(container, result, playerId) {
    console.log(`📍 Showing flip result in container for player ${playerId}`);
    
    const typeIcon = result.type === 'bomb' || result.type === 'system_bomb' ? '💣' : '💎';
    const valueText = result.value > 0 ? `+${result.value}` : '0';
    
    const resultElement = document.createElement('div');
    resultElement.className = 'flip-result-inline';
    resultElement.style.cssText = `
        background: ${result.type === 'bomb' || result.type === 'system_bomb' ? '#f8d7da' : '#d4edda'};
        border: 2px solid ${result.type === 'bomb' || result.type === 'system_bomb' ? '#dc3545' : '#28a745'};
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        text-align: center;
        font-weight: bold;
        z-index: 1000;
    `;
    resultElement.innerHTML = `${typeIcon} 翻牌结果: ${getCardTypeText(result.type)} 价值: ${valueText}`;
    
    container.appendChild(resultElement);
    console.log(`✅ Added inline flip result for player ${playerId}`);
    
    setTimeout(() => {
        if (resultElement.parentNode) {
            resultElement.remove();
            console.log(`Removed inline flip result for player ${playerId}`);
        }
    }, 10000);
}

// 直接在翻牌的卡牌位置显示结果
function showFlipResultDirectly(cardId, playerId, result) {
    console.log(`=== DIRECT FLIP RESULT === Card: ${cardId}, Player: ${playerId}, Result:`, result);
    
    // 查找玩家的整个抽牌区域容器
    const playerSection = document.getElementById(`player-cards-${playerId}`);
    if (!playerSection) {
        console.error(`Player section not found for player ${playerId}`);
        return;
    }
    
    // 移除之前的翻牌结果
    const existingResults = playerSection.querySelectorAll('.flip-result-banner');
    existingResults.forEach(el => el.remove());
    
    const typeIcon = result.type === 'bomb' || result.type === 'system_bomb' ? '💣' : '💎';
    const valueText = result.value > 0 ? `+${result.value}` : '0';
    
    const resultBanner = document.createElement('div');
    resultBanner.className = 'flip-result-banner';
    resultBanner.style.cssText = `
        background: ${result.type === 'bomb' || result.type === 'system_bomb' ? '#ffebee' : '#e8f5e8'};
        border: 3px solid ${result.type === 'bomb' || result.type === 'system_bomb' ? '#f44336' : '#4caf50'};
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        animation: flipResultPulse 2s ease-in-out;
        position: relative;
        z-index: 1000;
    `;
    
    resultBanner.innerHTML = `
        <div style="font-size: 24px; margin-bottom: 8px;">${typeIcon}</div>
        <div>翻牌结果: ${getCardTypeText(result.type)}</div>
        <div style="font-size: 20px; margin-top: 5px;">价值: ${valueText}</div>
    `;
    
    // 插入到玩家区域的顶部（在标题下方）
    const header = playerSection.querySelector('.player-cards-header');
    if (header && header.nextSibling) {
        playerSection.insertBefore(resultBanner, header.nextSibling);
    } else {
        playerSection.appendChild(resultBanner);
    }
    
    console.log(`✅ Added flip result banner for player ${playerId} in player section`);
    
    // 15秒后自动移除
    setTimeout(() => {
        if (resultBanner.parentNode) {
            resultBanner.remove();
            console.log(`Removed flip result banner for player ${playerId}`);
        }
    }, 15000);
}


// 更新已翻开卡牌的DOM
function updateFlippedCardDOM(cardId, result) {
    const cardElement = document.getElementById(`card-dom-${cardId}`);
    if (!cardElement) {
        console.error(`Card element with ID card-dom-${cardId} not found for DOM update.`);
        return;
    }

    console.log(`Updating DOM for card ${cardId} with result:`, result);

    // 清理并重置卡牌元素
    cardElement.innerHTML = '';
    cardElement.className = 'card'; // 重置基础类
    cardElement.onclick = null; // 禁用点击
    cardElement.style.cursor = 'default';
    cardElement.title = '';

    // 根据结果添加新样式和内容
    const typeClass = result.type === 'bomb' || result.type === 'system_bomb' ? 'bomb-card' : 'value-card';
    cardElement.classList.add(result.type, typeClass);

    const typeIcon = result.type === 'bomb' || result.type === 'system_bomb' ? '💣' : '💎';
    const valueDisplay = result.value > 0 ? `+${result.value}` : '0';

    cardElement.innerHTML = `
        <div class="card-icon">${typeIcon}</div>
        <div class="card-type">${getCardTypeText(result.type)}</div>
        <div class="card-value">${valueDisplay}</div>
        <div class="card-info">ID: ${result.id.substring(0, 8)}</div>
    `;
}

// 辅助函数
function toggleCardSelectionForPlayer(cardId, playerId) {
    if (selectedCards.has(cardId)) {
        selectedCards.delete(cardId);
    } else {
        selectedCards.add(cardId);
    }
    
    // 更新选择计数显示
    const countElement = document.getElementById(`selected-count-${playerId}`);
    if (countElement) {
        countElement.textContent = selectedCards.size;
    }
    
    // 重新加载该玩家的卡牌显示以更新选中状态
    loadPlayerCards(playerId);
}

function flipSelectedCardsForPlayer(playerId) {
    if (selectedCards.size === 0) {
        logMessage('请至少选择一张牌', 'warning');
        return;
    }

    const cardIds = Array.from(selectedCards);
    fetch('/api/flip-cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playerId, cardIds })
    }).then(response => response.json())
      .then(data => {
          if (!data.success) {
              logMessage(`翻牌失败: ${data.message}`, 'error');
          } else {
              // 显示翻牌结果
              displayFlipResults(playerId, data.results);
              selectedCards.clear();
              
              // 更新选择计数
              const countElement = document.getElementById(`selected-count-${playerId}`);
              if (countElement) {
                  countElement.textContent = '0';
              }
          }
      });
}

function displayFlipResults(playerId, results) {
    const resultsContainer = document.getElementById(`flip-results-${playerId}`);
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = '<h5>翻牌结果:</h5>';
    
    results.forEach(result => {
        const resultElement = document.createElement('div');
        resultElement.className = `flip-result ${result.type}`;
        
        let resultText = '';
        if (result.type === 'bomb' || result.type === 'system_bomb') {
            resultText = `💣 炸弹! (价值: ${result.value})`;
            resultElement.classList.add('bomb-result');
        } else if (result.type === 'value' || result.type === 'system_value') {
            resultText = `💎 价值牌! (价值: ${result.value})`;
            resultElement.classList.add('value-result');
        }
        
        resultElement.innerHTML = `
            <span class="card-id">牌 ${result.id.substring(0, 8)}</span>: ${resultText}
        `;
        resultsContainer.appendChild(resultElement);
    });
}

function setCurrentPlayer(playerId) {
    const oldPlayerId = currentPlayerId;
    currentPlayerId = playerId;
    
    // 清空选中的卡牌
    selectedCards.clear();
    
    // 更新UI显示
    updatePlayersCardsDisplay();
    
    logMessage(`切换操控玩家: ${getPlayerName(playerId)}`, 'info');
    
    // 显示翻牌操作面板
    showFlipPanel(playerId);
}

function showFlipPanel(playerId) {
    const player = gameState.players?.find(p => p.id === playerId);
    const hasDrawn = gameState.playersDrawnThisRound?.includes(playerId) || false;
    const hasActed = gameState.playersActedThisRound?.includes(playerId) || false;
    
    if (!player || !hasDrawn || hasActed) return;
    
    // 创建翻牌操作面板
    let panel = document.getElementById('flipPanel');
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'flipPanel';
        panel.className = 'flip-panel';
        document.body.appendChild(panel);
    }
    
    panel.innerHTML = `
        <div class="flip-panel-content">
            <h4>${player.name} - 翻牌操作</h4>
            <p>请选择要翻开的卡牌，然后点击翻牌按钮</p>
            <div id="flipPanelCards" class="flip-panel-cards"></div>
            <div class="flip-actions">
                <button class="btn btn-warning" onclick="flipSelectedCards()">翻牌</button>
                <button class="btn btn-danger" onclick="leaveGame()">离场</button>
                <button class="btn btn-secondary" onclick="closeFlipPanel()">取消</button>
            </div>
        </div>
    `;
    
    // 加载玩家的手牌到翻牌面板
    loadPlayerCardsToFlipPanel(playerId);
    
    panel.style.display = 'block';
}

function closeFlipPanel() {
    const panel = document.getElementById('flipPanel');
    if (panel) {
        panel.style.display = 'none';
    }
    currentPlayerId = null;
    selectedCards.clear();
    updatePlayersCardsDisplay();
}

function loadPlayerCardsToFlipPanel(playerId) {
    fetch(`/api/player-cards/${playerId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayCardsInFlipPanel(playerId, data.cards);
            }
        })
        .catch(error => {
            console.error('Failed to load player cards for flip panel:', error);
        });
}

function displayCardsInFlipPanel(playerId, cards) {
    const container = document.getElementById('flipPanelCards');
    if (!container) return;
    
    container.innerHTML = '';
    
    cards.forEach(card => {
        const cardElement = createCardElement(card, playerId);
        cardElement.classList.add('flip-panel-card');
        container.appendChild(cardElement);
    });
}

function getCurrentPlayer() {
    if (currentPlayerId) {
        return gameState.players?.find(p => p.id === currentPlayerId);
    }
    
    // 在竞拍阶段，返回当前竞拍玩家
    if (gameState.gameState === 'bidding' && gameState.players) {
        const currentIndex = gameState.currentPlayerIndex || 0;
        return gameState.players[currentIndex];
    }
    
    return gameState.players?.find(p => p.id === gameState.currentPlayer);
}

function getPlayerName(playerId) {
    const player = gameState.players?.find(p => p.id === playerId);
    return player ? player.name : '未知玩家';
}

function getGameStateText() {
    switch (gameState.gameState) {
        case 'waiting': return '等待开始';
        case 'bidding': return '竞拍阶段';
        case 'playing': return `游戏进行中 - 第${gameState.gameRound || 0}轮`;
        case 'finished': return '游戏结束';
        default: return '未知状态';
    }
}

function getRoundPhaseText(phase) {
    switch (phase) {
        case 'draw': return '抽牌阶段';
        case 'flip': return '翻牌阶段';
        case 'decide': return '决策阶段';
        default: return '未知阶段';
    }
}

function getPlayerActionButtons(player) {
    if (gameState.gameState !== 'playing' || player.role === 'landlord' || !player.isActive) {
        return '';
    }
    
    const hasDrawn = gameState.playersDrawnThisRound?.includes(player.id) || false;
    const hasActed = gameState.playersActedThisRound?.includes(player.id) || false;
    
    let buttons = '';
    
    if (gameState.roundPhase === 'draw' && !hasDrawn) {
        buttons += `<button class="btn btn-success btn-sm" onclick="drawCardsForPlayer('${player.id}')">抽牌</button>`;
    }
    
    // 移除翻牌按钮，翻牌操作在抽牌区域进行
    
    if (hasDrawn && !hasActed) {
        buttons += `<button class="btn btn-danger btn-sm" onclick="leaveGameForPlayer('${player.id}')">离场</button>`;
    }
    
    return buttons || '<span class="text-muted">等待中</span>';
}

function drawCardsForPlayer(playerId) {
    fetch('/api/draw-cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playerId })
    }).then(response => response.json())
      .then(data => {
          if (!data.success) {
              logMessage(`抽牌失败: ${data.message}`, 'error');
          }
      });
}

function leaveGameForPlayer(playerId) {
    const player = gameState.players?.find(p => p.id === playerId);
    if (player && confirm(`确定要让 ${player.name} 离场吗？`)) {
        fetch('/api/leave-game', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ playerId })
        }).then(response => response.json())
          .then(data => {
              if (!data.success) {
                  logMessage(`离场失败: ${data.message}`, 'error');
              }
          });
    }
}

function getCardTypeText(type) {
    switch (type) {
        case 'value': return '价值';
        case 'bomb': return '炸弹';
        case 'system_value': return '系统价值';
        case 'system_bomb': return '系统炸弹';
        default: return '未知';
    }
}

function logMessage(message, type = 'info') {
    const log = document.getElementById('gameLog');
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
}

// 更新调试指引
function updateDebugGuide() {
    const guideContainer = document.getElementById('debugGuide');
    if (!guideContainer) return;
    
    const guide = getDebugGuide();
    guideContainer.innerHTML = `
        <div class="debug-guide-content">
            <h4>🎯 当前环节指引</h4>
            <div class="guide-info">
                <div class="guide-stage">${guide.stage}</div>
                <div class="guide-description">${guide.description}</div>
            </div>
            <div class="guide-actions">
                <h5>📋 操作提示：</h5>
                <ul>
                    ${guide.actions.map(action => `<li>${action}</li>`).join('')}
                </ul>
            </div>
            ${guide.tips ? `
                <div class="guide-tips">
                    <h5>💡 提示：</h5>
                    <div class="tip-text">${guide.tips}</div>
                </div>
            ` : ''}
        </div>
    `;
}

// 获取调试指引信息
function getDebugGuide() {
    if (!gameState || !gameState.gameState) {
        return {
            stage: '等待开始',
            description: '游戏尚未初始化',
            actions: ['点击"开始新游戏"按钮初始化游戏'],
            tips: '游戏需要4名玩家参与，系统会自动创建玩家A、B、C、D'
        };
    }
    
    switch (gameState.gameState) {
        case 'waiting':
            return {
                stage: '等待开始',
                description: '游戏已重置，等待重新开始',
                actions: ['点击"开始新游戏"按钮重新初始化游戏'],
                tips: '重置后所有玩家状态将清空'
            };
            
        case 'bidding':
            const currentBidder = getCurrentBiddingPlayer();
            const biddingTurnCount = gameState.biddingInfo?.biddingTurnCount || 0;
            const remainingTurns = 5 - biddingTurnCount;
            return {
                stage: '地主竞拍阶段',
                description: `竞价进度：${biddingTurnCount}/5 (A→B→C→D→A)`,
                actions: [
                    `当前轮到：${currentBidder ? currentBidder.name : '未知玩家'}`,
                    `剩余竞价次数：${remainingTurns}次`,
                    '在竞拍区域输入出价金额（最低10积分）',
                    '点击"出价"按钮进行竞拍，或点击"放弃"跳过',
                    `当前最高价：${gameState.biddingInfo?.currentBid || 0}积分`,
                    `最高出价者：${gameState.biddingInfo?.currentBidder || '无'}`
                ],
                tips: '总共进行5次竞价操作，从玩家A开始到玩家A结束，最高出价者成为地主'
            };
            
        case 'playing':
            return getPlayingStageGuide();
            
        case 'finished':
            return {
                stage: '游戏结束',
                description: '本局游戏已结束',
                actions: [
                    '查看最终积分排名',
                    '点击"重置游戏"开始新的一局'
                ],
                tips: '零和博弈：所有玩家净收益总和为零'
            };
            
        default:
            return {
                stage: '未知状态',
                description: '游戏状态异常',
                actions: ['尝试重置游戏'],
                tips: '如果问题持续，请刷新页面'
            };
    }
}

// 获取游戏进行阶段的指引
function getPlayingStageGuide() {
    const activeFarmers = gameState.players?.filter(p => p.role === 'farmer' && p.isActive) || [];
    const landlord = gameState.players?.find(p => p.role === 'landlord');
    
    if (gameState.roundPhase === 'draw') {
        const waitingFarmers = activeFarmers.filter(p => !p.hasDrawnThisRound);
        return {
            stage: `第${gameState.gameRound}轮 - 抽牌阶段`,
            description: '农民进行抽牌操作',
            actions: [
                `地主：${landlord ? landlord.name : '无'} (观战中)`,
                `等待抽牌的农民：${waitingFarmers.map(p => p.name).join('、') || '无'}`,
                '点击农民卡片上的"抽牌"按钮进行抽牌',
                '每名农民每轮抽取5张牌（背面朝上）'
            ],
            tips: '所有农民完成抽牌后进入翻牌阶段'
        };
    } else if (gameState.roundPhase === 'flip') {
        const waitingFarmers = activeFarmers.filter(p => p.hasDrawnThisRound && !p.hasActedThisRound);
        return {
            stage: `第${gameState.gameRound}轮 - 翻牌阶段`,
            description: '农民选择翻牌或离场',
            actions: [
                `等待行动的农民：${waitingFarmers.map(p => p.name).join('、') || '无'}`,
                '点击"选择翻牌"按钮操控指定农民',
                '在弹出面板中选择要翻开的牌（至少1张）',
                '价值牌：获得积分，炸弹牌：立即离场',
                '也可选择"离场"保住当前收益'
            ],
            tips: '翻开价值牌后该牌价值归零，但玩家获得该牌的复制'
        };
    }
    
    return {
        stage: `第${gameState.gameRound}轮 - 游戏进行中`,
        description: '游戏正在进行',
        actions: ['等待玩家操作'],
        tips: '最多进行5轮，或所有农民离场后游戏结束'
    };
}

// 获取当前竞拍玩家
function getCurrentBiddingPlayer() {
    if (gameState.gameState !== 'bidding' || !gameState.players) return null;
    return gameState.players[gameState.currentPlayerIndex || 0];
}

// 页面加载完成后获取初始状态
window.addEventListener('load', () => {
    fetch('/api/game-state')
        .then(response => response.json())
        .then(data => {
            gameState = data;
            updateUI();
        });
});
