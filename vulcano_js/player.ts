// Player (WobblyBall) - Volcano Jump JS

export class Player {
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
    // Limiti bordo
    if (this.x - this.radius < 0) {
      this.x = this.radius;
      this.vx = Math.abs(this.vx) * 0.7;
    }
    if (this.x + this.radius > 600) {
      this.x = 600 - this.radius;
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
