from main import WIDTH, HEIGHT

px, py = WIDTH / 1024, HEIGHT / 768

maps = {
    "map1": [
        { "shape": "rect", "coords": [WIDTH / 5, HEIGHT / 3, WIDTH / 5 + px * 10, HEIGHT / 1.5], "fill": "gray", "mirrored": [WIDTH]},
        { "shape": "rect", "coords": [WIDTH / 5 + px * 100, HEIGHT / 1.5, WIDTH / 5 + px * 110, HEIGHT - py * 50], "fill": "gray", "mirrored": [WIDTH] },
        { "shape": "rect", "coords": [WIDTH / 2.7, HEIGHT / 1.3, WIDTH - WIDTH / 2.7, HEIGHT / 1.3 + py * 10], "fill": "gray", "mirrored": [HEIGHT] },
        { "shape": "rect", "coords": [WIDTH / 2 - px * 80, HEIGHT / 2 - px * 80, WIDTH / 2 - px * 70, HEIGHT / 2 + px * 80], "fill": "gray", "mirrored": [WIDTH] }
    ],

    "map2": [
        { "shape": "circle", "coords": [px * 150, px * 575], "radius": px * 50, "fill": "green", "mirrored": [WIDTH, HEIGHT], "tags": ["NoCollision"]},
        { "shape": "circle", "coords": [px * 200, px * 550], "radius": px * 50, "fill": "green", "mirrored": [WIDTH, HEIGHT], "tags": ["NoCollision"]},
        { "shape": "circle", "coords": [px * 160, px * 515], "radius": px * 50, "fill": "green", "mirrored": [WIDTH, HEIGHT], "tags": ["NoCollision"]},
        
        { "shape": "circle", "coords": [px * 300, px * 150], "radius": px * 50, "fill": "green", "mirrored": [WIDTH, HEIGHT], "tags": ["NoCollision"]},
        { "shape": "circle", "coords": [px * 250, px * 150], "radius": px * 50, "fill": "green", "mirrored": [WIDTH, HEIGHT], "tags": ["NoCollision"]},

        { "shape": "rect", "coords": [px * 300, px * 350, px * 350, px * 575], "fill": "LightSalmon4", "mirrored": [WIDTH, HEIGHT] }
    ]
}