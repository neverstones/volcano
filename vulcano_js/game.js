System.register(["./player", "./platform"], function (exports_1, context_1) {
    "use strict";
    var player_1, platform_1, WIDTH, HEIGHT, Game;
    var __moduleName = context_1 && context_1.id;
    return {
        setters: [
            function (player_1_1) {
                player_1 = player_1_1;
            },
            function (platform_1_1) {
                platform_1 = platform_1_1;
            }
        ],
        execute: function () {
            WIDTH = 600;
            HEIGHT = 800;
            Game = class Game {
                constructor(ctx) {
                    this.ctx = ctx;
                    this.player = new player_1.Player(WIDTH / 2, HEIGHT - 100);
                    this.platforms = [];
                    this.createPlatforms();
                }
                createPlatforms() {
                    this.platforms = [];
                    let y = HEIGHT - 50;
                    for (let i = 0; i < 20; i++) {
                        let x = Math.random() * (WIDTH - 120) + 10;
                        this.platforms.push(new platform_1.Platform(x, y));
                        y -= 80;
                    }
                }
                update() {
                    this.player.update();
                    // Collisione piattaforme
                    for (const plat of this.platforms) {
                        if (this.player.x + this.player.radius > plat.x &&
                            this.player.x - this.player.radius < plat.x + plat.width &&
                            this.player.y + this.player.radius > plat.y &&
                            this.player.y + this.player.radius < plat.y + plat.height &&
                            this.player.vy > 0) {
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
            };
            exports_1("Game", Game);
        }
    };
});
