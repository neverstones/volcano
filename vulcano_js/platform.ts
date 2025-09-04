// Platform - Volcano Jump JS

export class Platform {
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
