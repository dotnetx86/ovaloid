from main import WIDTH, HEIGHT

px, py = WIDTH / 1024, HEIGHT / 768

map1 = [
    { "shape": "rect", "coords": [WIDTH / 5, HEIGHT / 3, WIDTH / 5 + px * 10, HEIGHT / 1.5], "fill": "gray", "mirrored": [WIDTH]},
    { "shape": "rect", "coords": [WIDTH / 5 + px * 100, HEIGHT / 1.5, WIDTH / 5 + px * 110, HEIGHT - py * 50], "fill": "gray", "mirrored": [WIDTH] },
    { "shape": "rect", "coords": [WIDTH / 2.7, HEIGHT / 1.3, WIDTH - WIDTH / 2.7, HEIGHT / 1.3 + py * 10], "fill": "gray", "mirrored": [HEIGHT] },
    { "shape": "rect", "coords": [WIDTH / 2 - px * 80, HEIGHT / 2 - px * 80, WIDTH / 2 - px * 70, HEIGHT / 2 + px * 80], "fill": "gray", "mirrored": [WIDTH] }
]

map2 = [
    { "shape": "circle", "coords": [px * 140, px * 475, px * 50], "fill": "green", "mirrored": [], "tags": ["NoCollision"]},
]