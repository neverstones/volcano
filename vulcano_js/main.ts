
// Volcano Jump JS - Tutto in un unico file
const canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
const ctx = canvas.getContext('2d')!;
const WIDTH = 600;
const HEIGHT = 800;

enum GameState {
  MENU,
  PLAYING,
  GAME_OVER,
  LEADERBOARD,
  ENTER_NAME
}
let gameState: GameState = GameState.MENU;

// Player
class Player {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
  health: number;
  maxHealth: number;
  constructor(x: number, y: number, radius: number = 32, color: string = '#FFA500') {
    this.x = x;
    this.y = y;
    this.vx = 0;
    this.vy = 0;
    this.radius = radius;
    this.color = color;
    this.health = 3;
    this.maxHealth = 3;
  }
  update(gravity: number = 0.8, maxFall: number = 15) {
    this.vy = Math.min(this.vy + gravity, maxFall);
    this.x += this.vx;
    this.y += this.vy;
    if (this.x - this.radius < 0) {
      this.x = this.radius;
      this.vx = Math.abs(this.vx) * 0.7;
    }
    if (this.x + this.radius > WIDTH) {
      this.x = WIDTH - this.radius;
      this.vx = -Math.abs(this.vx) * 0.7;
    }
  }
  draw(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.shadowColor = '#FF6600';
    ctx.shadowBlur = 15;
    ctx.fill();
    ctx.closePath();
    ctx.restore();
  }
}

// Platform
class Platform {
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  constructor(x: number, y: number, width: number = 100, height: number = 16, color: string = '#FF6400') {
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
    this.color = color;
  }
  draw(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.fillStyle = this.color;
    ctx.fillRect(this.x, this.y, this.width, this.height);
    ctx.restore();
  }
}

// Game
class Game {
  ctx: CanvasRenderingContext2D;
  player: Player;
  platforms: Platform[];
  constructor(ctx: CanvasRenderingContext2D) {
    this.ctx = ctx;
    this.player = new Player(WIDTH/2, HEIGHT-100);
    this.platforms = [];
    this.createPlatforms();
  }
  createPlatforms() {
    this.platforms = [];
    let y = HEIGHT - 50;
    for (let i = 0; i < 20; i++) {
      let x = Math.random() * (WIDTH - 120) + 10;
      this.platforms.push(new Platform(x, y));
      y -= 80;
    }
  }
  update() {
    this.player.update();
    for (const plat of this.platforms) {
      if (
        this.player.x + this.player.radius > plat.x &&
        this.player.x - this.player.radius < plat.x + plat.width &&
        this.player.y + this.player.radius > plat.y &&
        this.player.y + this.player.radius < plat.y + plat.height &&
        this.player.vy > 0
      ) {
        this.player.y = plat.y - this.player.radius;
        this.player.vy = -14;
      }
    }
  }
  draw() {
    for (const plat of this.platforms) {
      plat.draw(this.ctx);
    }
    this.player.draw(this.ctx);
  }
}

let game: Game = new Game(ctx);

function gameLoop() {
  ctx.clearRect(0, 0, WIDTH, HEIGHT);
  if (gameState === GameState.PLAYING) {
    game.update();
    game.draw();
  } else if (gameState === GameState.MENU) {
    ctx.fillStyle = '#321a1a';
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    ctx.font = 'bold 48px Arial';
    ctx.fillStyle = '#ff9900';
    ctx.textAlign = 'center';
    ctx.fillText('VOLCANO JUMP', WIDTH/2, 180);
    ctx.font = '24px Arial';
    ctx.fillStyle = '#fff';
    ctx.fillText('Premi SPAZIO per giocare', WIDTH/2, 260);
    // Messaggio di debug visibile
    ctx.font = '20px Arial';
    ctx.fillStyle = '#0f0';
    ctx.fillText('DEBUG: Rendering attivo', WIDTH/2, 400);
  }
  requestAnimationFrame(gameLoop);
}



window.addEventListener('keydown', (e) => {
  if (gameState === GameState.MENU && e.code === 'Space') {
    gameState = GameState.PLAYING;
  }
  if (gameState === GameState.PLAYING) {
    if (e.code === 'ArrowLeft' || e.code === 'KeyA') {
      game.player.vx = -6;
    }
    if (e.code === 'ArrowRight' || e.code === 'KeyD') {
      game.player.vx = 6;
    }
    if (e.code === 'Space') {
      if (game.player.vy === 0) {
        game.player.vy = -14;
      }
    }
  }
});
window.addEventListener('keyup', (e) => {
  if (gameState === GameState.PLAYING) {
    if (e.code === 'ArrowLeft' || e.code === 'KeyA' || e.code === 'ArrowRight' || e.code === 'KeyD') {
      game.player.vx = 0;
    }
  }
});
