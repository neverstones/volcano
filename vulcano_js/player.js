// Player (WobblyBall) - Volcano Jump JS
System.register([], function (exports_1, context_1) {
    "use strict";
    var Player;
    var __moduleName = context_1 && context_1.id;
    return {
        setters: [],
        execute: function () {// Player (WobblyBall) - Volcano Jump JS
            Player = class Player {
                constructor(x, y, radius = 32, color = '#FFA500') {
                    this.x = x;
                    this.y = y;
                    this.vx = 0;
                    this.vy = 0;
                    this.radius = radius;
                    this.color = color;
                    this.health = 3;
                    this.maxHealth = 3;
                }
                update(gravity = 0.8, maxFall = 15) {
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
                draw(ctx) {
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
            };
            exports_1("Player", Player);
        }
    };
});
