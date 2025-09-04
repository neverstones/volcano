// Platform - Volcano Jump JS
System.register([], function (exports_1, context_1) {
    "use strict";
    var Platform;
    var __moduleName = context_1 && context_1.id;
    return {
        setters: [],
        execute: function () {// Platform - Volcano Jump JS
            Platform = class Platform {
                constructor(x, y, width = 100, height = 16, color = '#FF6400') {
                    this.x = x;
                    this.y = y;
                    this.width = width;
                    this.height = height;
                    this.color = color;
                }
                draw(ctx) {
                    ctx.save();
                    ctx.fillStyle = this.color;
                    ctx.fillRect(this.x, this.y, this.width, this.height);
                    ctx.restore();
                }
            };
            exports_1("Platform", Platform);
        }
    };
});
