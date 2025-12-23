# 游戏逻辑修复与增强需求文档

## 介绍

通过对比产品文档、接口文档、UML设计图和当前代码实现，发现了一些关键的游戏逻辑实现与设计文档不一致的问题。本需求文档按照UML图的模块结构，针对GameEngine、Player、Card等核心组件进行分块测试和修复，确保代码实现与游戏设计规则保持一致。

## 需求

### 需求 1 - GameEngine竞拍模块测试与修复

**用户故事：** 作为开发者，我希望GameEngine的竞拍逻辑模块能够正确实现产品文档规定的竞拍规则，以便通过分块测试验证其正确性

#### 验收标准

1. WHEN 调用`initializeGame()`方法 THEN GameEngine SHALL 正确初始化竞拍状态，设置`gameState='bidding'`和`biddingTurnCount=0`
2. WHEN 调用`placeBid(playerId, amount)`方法 THEN 系统 SHALL 验证当前玩家轮次、出价金额，并正确更新`currentBid`和`currentBidder`
3. WHEN `biddingTurnCount`达到5次 THEN `endBidding()`方法 SHALL 被自动调用，正确设置地主角色或无地主模式
4. WHEN 竞拍结束后 THEN `regenerateCardDeckAfterBidding()`方法 SHALL 被调用，重新生成符合产品文档规则的牌库

### 需求 2 - Card和牌库管理模块测试与修复

**用户故事：** 作为开发者，我希望Card类和牌库管理逻辑能够正确实现零和博弈机制，以便通过单元测试验证价值分配的准确性

#### 验收标准

1. WHEN 调用`generateCardDeck()`方法 THEN 系统 SHALL 创建25张Card对象，每张牌具有正确的`type`、`originalValue`、`currentValue`和`originalOwner`属性
2. WHEN 调用`redistributeValues()`方法 THEN 系统 SHALL 根据地主状态正确分配价值：有地主时15张价值牌(300)+5张炸弹牌+5张系统价值牌(100+出价)，无地主时20张价值牌(400)+5张系统炸弹牌
3. WHEN 调用Card的`flip()`方法 THEN 价值牌 SHALL 返回`originalValue`并将`currentValue`设为0，炸弹牌 SHALL 返回0
4. WHEN 调用Card的`copy()`方法 THEN 系统 SHALL 创建新的Card实例，保持`originalValue`不变，用于玩家手牌

### 需求 3 - Player模块测试与修复

**用户故事：** 作为开发者，我希望Player类的手牌管理和积分计算逻辑能够正确实现产品文档规定的农民手牌机制，以便通过模块测试验证其准确性

#### 验收标准

1. WHEN 调用Player的`addCardToHand(card)`方法 THEN 系统 SHALL 将Card的副本添加到`handCards`数组，保持副本的`originalValue`不变
2. WHEN 调用Player的`getHandValue()`方法 THEN 系统 SHALL 返回`handCards`中所有价值牌的`originalValue`总和
3. WHEN 调用Player的`getFinalScore()`方法 THEN 农民 SHALL 返回`getHandValue() - entryFee`，地主 SHALL 返回`landlordRevenue - entryFee - bidAmount`
4. WHEN Player的`isActive`设为false时 THEN 系统 SHALL 正确处理玩家离场状态，保持其`handCards`和抽牌历史`drawnCards`不变

### 需求 4 - GameEngine游戏流程模块测试与修复

**用户故事：** 作为开发者，我希望GameEngine的抽牌、翻牌、回合管理等游戏流程模块能够正确实现产品文档规定的游戏规则，以便通过集成测试验证完整流程

#### 验收标准

1. WHEN 调用`drawCards(playerId)`方法 THEN 系统 SHALL 修复防重复抽牌逻辑，确保5轮游戏中玩家始终能抽到5张牌，可能需要将`drawnCards`改为按轮次管理或实现牌库循环机制
2. WHEN 调用`flipCards(playerId, cardIds)`方法 THEN 系统 SHALL 验证cardIds属于玩家本轮抽牌，正确处理价值牌复制和炸弹牌离场逻辑
3. WHEN 调用`nextRound()`方法 THEN 系统 SHALL 正确清理`playersDrawnThisRound`、`playersActedThisRound`和所有玩家的`currentRoundCards`，并根据新的防重复策略重置相关状态
4. WHEN 调用`resetGame()`方法 THEN 系统 SHALL 移除废弃的`drawnCardsThisRound`引用，正确重置所有游戏状态，包括玩家的`drawnCards`集合

### 需求 5 - API接口层与前后端数据同步修复

**用户故事：** 作为开发者，我希望API接口能够提供准确的数据，确保前端能够正确识别和显示每个玩家的操作结果

#### 验收标准

1. WHEN POST `/api/flip-cards`返回翻牌结果时 THEN 响应数据 SHALL 包含明确的`playerId`信息，确保前端能够将结果显示在正确的玩家区域
2. WHEN GET `/api/player-cards/:playerId`接收到请求 THEN 系统 SHALL 验证playerId的有效性，返回准确的玩家卡牌信息，避免返回其他玩家的数据
3. WHEN Socket.IO广播`cardsFlipped`事件时 THEN 事件数据 SHALL 包含完整的`playerId`、`results`和上下文信息，确保前端能够正确处理和显示
4. WHEN 前端请求特定玩家数据时 THEN API SHALL 提供数据验证机制，确保返回的数据与请求的playerId完全匹配，避免数据混乱

### 需求 6 - 前端翻牌结果显示修复与玩家区域同步

**用户故事：** 作为游戏玩家，我希望翻牌结果能够持续显示在正确的玩家区域，不会出现显示错乱或结果消失的问题

#### 验收标准

1. WHEN 玩家执行翻牌操作 THEN 翻牌结果 SHALL 持续显示在对应玩家的区域内，不会自动消失或显示在错误的玩家区域
2. WHEN 调用`showFlipResultInPlayerArea(playerId, result)`时 THEN 系统 SHALL 确保结果容器`flip-results-${playerId}`正确关联到对应玩家，避免playerId混乱导致的显示错误
3. WHEN 多个翻牌结果需要显示时 THEN 系统 SHALL 正确管理结果容器的创建和清理，避免DOM元素冲突和内存泄漏
4. WHEN 卡牌DOM更新时 THEN `updateFlippedCardDOM(cardId, result)`方法 SHALL 正确找到对应的卡牌元素并更新其显示状态，确保卡牌ID与DOM元素ID的映射关系正确

### 需求 7 - 防重复抽牌机制修复与牌库可持续性保证

**用户故事：** 作为游戏玩家，我希望在5个回合的游戏过程中始终能够正常抽牌，不会因为防重复机制导致可用牌数不足的问题

#### 验收标准

1. WHEN 游戏进行多轮后 THEN 系统 SHALL 确保每个玩家在每轮都能抽到5张牌，可用牌池数量始终足够支持正常游戏流程
2. WHEN 玩家抽牌时 THEN 系统 SHALL 实现合理的防重复策略，可能需要修改为"本轮内不重复"而非"历史永不重复"，或实现牌库循环利用机制
3. WHEN 计算可用牌池时 THEN 系统 SHALL 考虑牌库容量限制（25张）与游戏需求（5轮×4人×5张=100张次）的数学关系，确保逻辑可行性
4. WHEN 牌被还回牌库时 THEN 系统 SHALL 正确管理牌的可用状态，确保还回的牌能够在后续轮次中被重新抽取（除非有特殊规则限制）

### 需求 8 - 调试工具和自动化验证系统

**用户故事：** 作为开发者，我希望有完善的调试工具和自动化验证系统，以便实时监控游戏状态、验证逻辑一致性，并快速定位问题

#### 验收标准

1. WHEN 开发者打开调试面板 THEN 系统 SHALL 显示分模块的游戏状态信息，包括GameEngine状态、Player详情、Card牌库分析、零和平衡验证
2. WHEN 游戏状态更新时 THEN 调试系统 SHALL 自动运行一致性检查，验证牌库完整性、玩家状态合法性、价值分配正确性
3. WHEN 发现逻辑错误时 THEN 调试面板 SHALL 按模块分类显示错误信息，提供具体的修复建议和相关代码位置
4. WHEN 开发者需要测试时 THEN 系统 SHALL 提供预设测试场景，支持单模块测试、集成测试和完整游戏流程测试