// Logica principale Volcano Jump JS
import { Player } from './player';
import { Platform } from './platform';

const WIDTH = 600;
const HEIGHT = 800;

export class Game {
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
    // Collisione piattaforme
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
