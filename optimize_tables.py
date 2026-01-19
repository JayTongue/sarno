import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize
import json


def gaussian(eval_point, tab_point, radius=5, tab_scale=3):
    ex, ey = eval_point ; tx, ty = tab_point
    numerator = -((ex-tx)**2+(ey-ty)**2)
    denominator = tab_scale**2*radius**2
    return np.exp(numerator / denominator)


def iterate_points(eval_point, tab_points):
    vals = list(map(gaussian, [eval_point]*len(tab_points), tab_points))
    return max(vals)


def riemann_sum(room, tab_points: list, presentation_corner):
    roomw, roomh = room.shape
    meshx = np.arange(0, roomw) ; meshy = np.arange(0, roomh)
    meshx, meshy = np.meshgrid(meshx, meshy)
    max_influence = np.zeros_like(meshx)
    if presentation_corner:
        tab_points.append((0, 0))
    for tabx, taby in tab_points:
        val = gaussian((meshx, meshy), (tabx, taby))
        max_influence = np.maximum(max_influence, val)
    return max_influence, np.sum(max_influence)


def visualize(max_influence: np.array, tab_points, tab_rad=5):
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(max_influence.T, origin='lower', cmap='viridis', aspect='equal')
    for tab_point in tab_points:
        tab_point = tab_point[::-1]
        circ = plt.Circle(tab_point, tab_rad, fill=False)
        ax.add_patch(circ)
    ax.set_xlabel('x (ft)')
    ax.set_ylabel('y (ft)')
    ax.set_title('Height Field (Top View)')
    plt.colorbar(im, ax=ax, label='h(x,y)')

    plt.savefig('output/tabel_graph.png', format='png', bbox_inches='tight')
    plt.show()


def objective_function(p, room_size, radius, tab_scale, presentation_corner):
    n_tables = len(p) // 2
    tab_points = [(p[2*i], p[2*i+1]) for i in range(n_tables)]
    room = np.zeros(room_size)
    max_influence, integral = riemann_sum(room, tab_points, presentation_corner)
    return -integral


def constraint_no_overlap(p, radius):
    n_tables = len(p) // 2
    min_dist = float('inf')
    for i in range(n_tables):
        for j in range(i+1, n_tables):
            x1, y1 = p[2*i], p[2*i+1]
            x2, y2 = p[2*j], p[2*j+1]
            dist = np.sqrt((x1-x2)**2 + (y1-y2)**2)
            min_dist = min(min_dist, dist)
    
    return min_dist - 2*radius


def optimize_tables(room_size, n_tables=4, radius=2.5, tab_scale=3, presentation_corner=False):
    W, H = room_size
    
    initial = []
    for i in range(n_tables):
        x = (i % 2 + 1) * W / 3
        y = (i // 2 + 1) * H / 3
        initial.extend([x, y])

    initial = np.array(initial)
    
    bounds = []
    for i in range(n_tables):
        bounds.append((radius, W - radius)) ; bounds.append((radius, H - radius))

    constraints = {
        'type': 'ineq',
        'fun': constraint_no_overlap,
        'args': (radius,)
    }
    
    result = minimize(
        objective_function,
        initial,
        args=(room_size, radius, tab_scale, presentation_corner),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 100, 'disp': True, 'ftol': 1e-6},
    )
    
    optimal_positions = [(result.x[2*i], result.x[2*i+1]) for i in range(n_tables)]
    optimal_integral = -result.fun  # Negate back
    
    return optimal_positions, optimal_integral, result


if __name__ == '__main__':
    room_size = (20, 25)
    presentation_corner=True
    n_tables = 5
    radius = 2
    tab_scale = 2
    optimal_positions, max_integral, result = optimize_tables(
        room_size, 
        n_tables=n_tables, 
        radius=radius, 
        tab_scale=tab_scale,
        presentation_corner=presentation_corner
    )

    result_dict = {k: v for k, v in enumerate(optimal_positions)}
    with open('output/table_coords.json', 'w') as outfile:
        json.dump(result_dict, outfile, indent=4)
    print(result_dict)

    room = np.zeros(room_size)
    max_influence, integral = riemann_sum(room, optimal_positions, presentation_corner)
    visualize(max_influence, optimal_positions, tab_rad=2.5)