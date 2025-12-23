# 抽牌游戏 UML 设计图

## 1. 系统架构图

```mermaid

graph TB

    subgraph "客户端层"

        A[Web浏览器]

        B[游戏界面]

        C[Socket.IO客户端]

    end

  

    subgraph "服务器层"

        D[Express服务器]

        E[Socket.IO服务器]

        F[游戏引擎]

        G[路由控制器]

    end

  

    subgraph "业务逻辑层"

        H[GameEngine]

        I[Player]

        J[Card]

        K[房间管理]

    end

  

    subgraph "数据层"

        L[内存状态]

        M[游戏日志]

    end

  

    A --> D

    A --> E

    B --> C

    C --> E

    D --> G

    E --> F

    G --> H

    F --> H

    H --> I

    H --> J

    H --> K

    H --> L

    F --> M

```

## 2. 核心类图

```mermaid

classDiagram

    class GameEngine {

        -players: Player[]

        -cardDeck: Card[]

        -gameState: string

        -currentPlayerIndex: number

        -biddingRound: number

        -currentBid: number

        -landlord: Player

        -totalPool: number

        -gameRound: number

      

        +initializeGame(playerNames: string[]): GameState

        +placeBid(playerId: string, amount: number): Result

        +drawCards(playerId: string): Result

        +flipCards(playerId: string, cardIds: string[]): Result

        +leaveGame(playerId: string): Result

        +endFlipping(playerId: string): Result

        +getGameState(): GameState

        +resetGame(): void

        -generateCardDeck(): void

        -redistributeValues(): void

        -nextRound(): void

        -endGame(): void

    }

  

    class Player {

        -id: string

        -name: string

        -role: string

        -handCards: Card[]

        -drawnCards: Set~string~

        -currentRoundCards: string[]

        -isActive: boolean

        -roundCount: number

        -bidAmount: number

        -entryFee: number

      

        +addCardToHand(card: Card): void

        +getHandValue(): number

        +getFinalScore(): number

        +reset(): void

    }

  

    class Card {

        -id: string

        -type: string

        -originalValue: number

        -currentValue: number

        -isFlipped: boolean

        -originalOwner: string

      

        +flip(): number

        +resetFlipState(): void

        +copy(): Card

    }

  

    class ExpressServer {

        -app: Express

        -server: HttpServer

        -io: SocketIOServer

        -gameEngine: GameEngine

      

        +setupRoutes(): void

        +setupSocketHandlers(): void

        +start(port: number): void

    }

  

    GameEngine "1" --> "*" Player : manages

    GameEngine "1" --> "*" Card : contains

    Player "1" --> "*" Card : holds

    ExpressServer "1" --> "1" GameEngine : uses

```

## 3. 游戏状态图

```mermaid

stateDiagram-v2

    [*] --> Waiting : 服务器启动

  

    Waiting --> Bidding : initializeGame()

  

    state Bidding {

        [*] --> PlayerTurn

        PlayerTurn --> PlayerTurn : placeBid()

        PlayerTurn --> BiddingEnd : 5轮竞拍完成

    }

  

    Bidding --> Playing : 竞拍结束

  

    state Playing {

        [*] --> DrawPhase

        DrawPhase --> FlipPhase : 所有农民抽牌完成

        FlipPhase --> DrawPhase : 回合结束，进入下一轮

        FlipPhase --> GameEnd : 所有农民离场

        DrawPhase --> GameEnd : 达到最大回合数

    }

  

    Playing --> Finished : 游戏结束

    Finished --> Waiting : resetGame()

```

## 4. 抽牌翻牌时序图

```mermaid

sequenceDiagram

    participant C as 客户端

    participant S as Express服务器

    participant G as GameEngine

    participant P as Player

    participant D as CardDeck

    participant IO as Socket.IO

  

    Note over C,IO: 抽牌流程

    C->>S: POST /api/draw-cards

    S->>G: drawCards(playerId)

    G->>P: 检查玩家状态

    G->>D: 获取可用牌池

    D-->>G: 返回可抽牌列表

    G->>G: 随机选择5张牌

    G->>P: 记录抽牌历史

    G-->>S: 返回抽牌结果

    S-->>C: 响应抽牌成功

    S->>IO: emit('gameStateUpdate')

    IO-->>C: 广播游戏状态更新

  

    Note over C,IO: 翻牌流程

    C->>S: POST /api/flip-cards

    S->>G: flipCards(playerId, cardIds)

    G->>P: 验证翻牌权限

    loop 每张选中的牌

        G->>D: 翻开指定卡牌

        D-->>G: 返回卡牌类型和价值

        alt 价值牌

            G->>P: 添加到手牌

        else 炸弹牌

            G->>P: 设置玩家离场

            break 停止翻牌

        end

    end

    G->>G: 检查游戏结束条件

    G-->>S: 返回翻牌结果

    S-->>C: 响应翻牌结果

    S->>IO: emit('cardsFlipped')

    IO-->>C: 广播翻牌事件

```

## 5. 竞拍流程时序图

```mermaid

sequenceDiagram

    participant C1 as 玩家A客户端

    participant C2 as 玩家B客户端

    participant C3 as 玩家C客户端

    participant C4 as 玩家D客户端

    participant S as Express服务器

    participant G as GameEngine

    participant IO as Socket.IO

  

    Note over C1,IO: 竞拍阶段开始

    S->>IO: emit('gameStateUpdate', {gameState: 'bidding'})

    IO-->>C1: 通知竞拍开始

    IO-->>C2: 通知竞拍开始

    IO-->>C3: 通知竞拍开始

    IO-->>C4: 通知竞拍开始

  

    Note over C1,IO: 玩家A出价

    C1->>S: POST /api/place-bid {amount: 20}

    S->>G: placeBid(playerA, 20)

    G->>G: 更新当前最高价

    G->>G: 切换到下一个玩家

    G-->>S: 返回竞拍结果

    S->>IO: emit('gameStateUpdate')

    IO-->>C1: 广播竞拍更新

    IO-->>C2: 广播竞拍更新

    IO-->>C3: 广播竞拍更新

    IO-->>C4: 广播竞拍更新

  

    Note over C1,IO: 玩家B出价

    C2->>S: POST /api/place-bid {amount: 30}

    S->>G: placeBid(playerB, 30)

    G->>G: 更新当前最高价和出价者

    G-->>S: 返回竞拍结果

    S->>IO: emit('gameStateUpdate')

    IO-->>C1: 广播竞拍更新

    IO-->>C2: 广播竞拍更新

    IO-->>C3: 广播竞拍更新

    IO-->>C4: 广播竞拍更新

  

    Note over C1,IO: 其他玩家放弃，竞拍结束

    C3->>S: POST /api/place-bid {amount: 0}

    C4->>S: POST /api/place-bid {amount: 0}

    C1->>S: POST /api/place-bid {amount: 0}

    S->>G: 检查竞拍结束条件

    G->>G: 设置玩家B为地主

    G->>G: 切换游戏状态为playing

    S->>IO: emit('gameStateUpdate', {gameState: 'playing'})

    IO-->>C1: 通知游戏开始

    IO-->>C2: 通知游戏开始

    IO-->>C3: 通知游戏开始

    IO-->>C4: 通知游戏开始

```

## 6. 数据流图

```mermaid

graph LR

    subgraph "输入数据"

        A[玩家操作]

        B[HTTP请求]

        C[Socket连接]

    end

  

    subgraph "处理层"

        D[路由处理]

        E[游戏引擎]

        F[业务逻辑]

    end

  

    subgraph "数据存储"

        G[游戏状态]

        H[玩家数据]

        I[牌库数据]

    end

  

    subgraph "输出数据"

        J[HTTP响应]

        K[Socket事件]

        L[游戏状态更新]

    end

  

    A --> B

    A --> C

    B --> D

    C --> D

    D --> E

    E --> F

    F --> G

    F --> H

    F --> I

    G --> E

    H --> E

    I --> E

    E --> J

    E --> K

    K --> L

```

## 7. 组件交互图

```mermaid

graph TB

    subgraph "前端组件"

        UI[用户界面]

        SC[Socket客户端]

        AC[API客户端]

    end

  

    subgraph "后端组件"

        ES[Express服务器]

        SS[Socket.IO服务器]

        GE[游戏引擎]

        RC[路由控制器]

    end

  

    subgraph "数据模型"

        PM[Player模型]

        CM[Card模型]

        GM[Game模型]

    end

  

    UI --> AC

    UI --> SC

    AC --> ES

    SC --> SS

    ES --> RC

    SS --> GE

    RC --> GE

    GE --> PM

    GE --> CM

    GE --> GM

  

    SS -.->|实时事件| SC

    ES -.->|HTTP响应| AC

```

## 8. 错误处理流程图

```mermaid

flowchart TD

    A[接收请求] --> B{验证请求参数}

    B -->|无效| C[返回400错误]

    B -->|有效| D{检查游戏状态}

    D -->|状态错误| E[返回业务错误]

    D -->|状态正确| F{验证玩家权限}

    F -->|权限不足| G[返回权限错误]

    F -->|权限正确| H[执行游戏逻辑]

    H --> I{执行成功?}

    I -->|失败| J[记录错误日志]

    I -->|成功| K[更新游戏状态]

    J --> L[返回500错误]

    K --> M[广播状态更新]

    M --> N[返回成功响应]

  

    C --> O[客户端错误处理]

    E --> O

    G --> O

    L --> O

    N --> P[客户端更新UI]

```

## 9. 部署架构图

```mermaid

graph TB

    subgraph "客户端"

        A[Web浏览器]

        B[移动浏览器]

    end

  

    subgraph "负载均衡"

        C[Nginx/负载均衡器]

    end

  

    subgraph "应用服务器"

        D[Node.js实例1]

        E[Node.js实例2]

        F[Node.js实例N]

    end

  

    subgraph "数据存储"

        G[Redis缓存]

        H[MongoDB数据库]

        I[日志文件]

    end

  

    subgraph "监控"

        J[应用监控]

        K[性能监控]

        L[错误追踪]

    end

  

    A --> C

    B --> C

    C --> D

    C --> E

    C --> F

    D --> G

    D --> H

    D --> I

    E --> G

    E --> H

    E --> I

    F --> G

    F --> H

    F --> I

  

    D --> J

    E --> J

    F --> J

    D --> K

    E --> K

    F --> K

    D --> L

    E --> L

    F --> L

```

---

*文档版本: v1.0*

*最后更新: 2025-09-02*
