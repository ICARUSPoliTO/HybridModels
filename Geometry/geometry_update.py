"""
This script provides the functions to update the geometry of a fuel grain.
"""
import numpy as np
import matplotlib.pyplot as plt
import Geometry.geometry_calculation as geomcalc

# ---------- helper ----------
def remove_close_vertices(x, y, tol=1e-12):
    pts = np.column_stack((np.asarray(x, float), np.asarray(y, float)))
    if pts.shape[0] == 0:
        return np.array([]), np.array([])
    keep = [0]
    for i in range(1, pts.shape[0]):
        if np.hypot(*(pts[i] - pts[keep[-1]])) > tol:
            keep.append(i)
    pts2 = pts[keep]
    return pts2[:, 0], pts2[:, 1]

def remove_collinear_simple(x, y, tol=1e-12):
    """
    Rimuove punti collineari consecutivi (semplice passaggio).
    Mantiene ordine e chiusura logica.
    """
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    if x.size < 3:
        return x.copy(), y.copy()
    # ensure closed indexing for checks
    N = x.size
    keep = []
    for i in range(N):
        im = (i - 1) % N
        ip = (i + 1) % N
        ux, uy = x[i] - x[im], y[i] - y[im]
        vx, vy = x[ip] - x[i], y[ip] - y[i]
        # cross product
        cross = ux * vy - uy * vx
        if abs(cross) > tol:
            keep.append(i)
    if len(keep) < 3:
        # fallback: return original if too aggressive
        return x, y
    x_new = x[keep];
    y_new = y[keep]
    return x_new, y_new

def remove_samearc_simple(x, y, tol=1e-12):
    """
    Rimuove punti sullo stesso arco consecutivi (semplice passaggio).
    Mantiene ordine e chiusura logica.
    """
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    if x.size < 3:
        return x.copy(), y.copy()
    # ensure closed indexing for checks
    N = x.size
    keep = []
    for i in range(N):
        im = (i - 1) % N
        ip = (i + 1) % N
        rm = np.hypot(x[im], y[im])
        r = np.hypot(x[i], y[i])
        rp = np.hypot(x[ip], y[ip])
        # cross product

        if not (np.isclose(r, rm, atol=tol) & np.isclose(r, rp, atol=tol)):
            keep.append(i)

    x_new = x[keep];
    y_new = y[keep]
    if x_new.size < 3:
        try:
            x_new, y_new = x[0], y[0]
        except:
            x_new, y_new = x, y

    return x_new, y_new

def _line_intersection_from_dirs(pA, vA, pB, vB, eps=1e-12):
    """
    Solve pA + s*vA = pB + t*vB for s,t.
    Returns (ok, point, s, t, cond) where ok is True if solution accepted.
    """
    A = np.column_stack((vA, vB))  # 2x2
    b = pB - pA
    det = np.linalg.det(A)
    cond = np.linalg.cond(A) if np.isfinite(det) else np.inf
    if abs(det) < eps or cond > 1e12:
        # try least squares
        try:
            sol, *_ = np.linalg.lstsq(A, b, rcond=None)
            s, t = float(sol[0]), float(sol[1])
            pt = pA + s * vA
            return True, pt, s, t, cond
        except Exception:
            return False, None, None, None, cond
    else:
        sol = np.linalg.solve(A, b)
        s, t = float(sol[0]), float(sol[1])
        pt = pA + s * vA
        return True, pt, s, t, cond

# ---------- main: burn_surface_v4 ----------
def burn_surface(x, y, z, regression_rate, dt,
                    min_param=1e-9, parallel_dot_thresh=0.9999,
                    close_tol=1e-12, merge_tol=1e-9):
    """
    Trasla i midpoint dei lati e trova le intersezioni tramite le tangenti.
    - x,y: contorno (1D arrays, ordine poligono)
    - z: +1/-1 per orientazione normale (normale = rotate tangente by +90 * z)
    - regression_rate, dt -> d = regression_rate * dt
    Returns: x_new, y_new
    info contains diagnostics: conds, fallbacks, midpoints, moved_midpoints
    """
    info = {}
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    if x.size < 3:
        return np.array([]), np.array([])

    # 0) cleanup duplicates
    x, y = remove_close_vertices(x, y, tol=close_tol)
    x, y = remove_collinear_simple(x, y, tol=close_tol)
    if x.size < 3:
        return np.array([]), np.array([])

    # 1) compute edges and midpoints
    x2 = np.r_[x, x[0]];
    y2 = np.r_[y, y[0]]
    dx = np.diff(x2);
    dy = np.diff(y2)
    edge_len = np.hypot(dx, dy)
    # protect division
    edge_len_safe = edge_len.copy()
    edge_len_safe[edge_len_safe == 0] = 1.0

    # tangents unitari (da vertice i a i+1)
    tx = dx / edge_len_safe
    ty = dy / edge_len_safe
    tang = np.column_stack((tx, ty))

    # midpoints dei lati
    xM = 0.5 * (x2[:-1] + x2[1:])
    yM = 0.5 * (y2[:-1] + y2[1:])

    # --- assicurati che z sia per-edge ---
    z = np.asarray(z).ravel()
    if z.size == 1:
        z = np.ones(xM.shape[0], dtype=float) * z[0]
    elif z.size != xM.shape[0]:
        # se z è per-vertice, converti a per-edge (es. take z at edge start)
        if z.size == x.size:
            z = z  # se vuoi usare per-vertex, mappa opportunamente
        else:
            z = np.resize(z, xM.shape[0])

    # normals (rotate tangenti +90 deg) e applica z
    normals = np.column_stack((ty * z, -tx * z))
    # normalizza normals per sicurezza e gestisci edge quasi nulli
    n_norm = np.hypot(normals[:, 0], normals[:, 1])
    small_edge_mask = (edge_len < 1e-12)
    n_norm[n_norm == 0] = 1.0
    normals[:, 0] /= n_norm
    normals[:, 1] /= n_norm

    # forza direzione verso l'esterno usando il centroide
    """
    cx = np.mean(x)
    cy = np.mean(y)
    centroid = np.array([cx, cy])
    for i_edge in range(normals.shape[0]):
        mid = np.array([xM[i_edge], yM[i_edge]])
        if np.dot(mid - centroid, normals[i_edge]) < 0:
            normals[i_edge] *= -1.0
    """

    # 2) move midpoints along normals con clamp locale
    d = float(regression_rate) * float(dt)
    # clamp factor: frazione della lunghezza minima degli spigoli adiacenti
    clamp_factor = 0.4
    xM_moved = np.empty_like(xM)
    yM_moved = np.empty_like(yM)
    xM_moved = xM + d * normals[:, 0]
    yM_moved = yM + d * normals[:, 1]
    """
    for i_edge in range(xM.size):
        # calcola una d locale basata sulla lunghezza dell'edge
        local_len = edge_len[i_edge] if edge_len[i_edge] > 0 else 1.0
        d_local = min(d, clamp_factor * local_len)

        # se edge troppo corto, evita spostamento e segnala
        if small_edge_mask[i_edge]:
            xM_moved[i_edge] = xM[i_edge]
            yM_moved[i_edge] = yM[i_edge]
        else:
            xM_moved[i_edge] = xM[i_edge] + d_local * normals[i_edge, 0]
            yM_moved[i_edge] = yM[i_edge] + d_local * normals[i_edge, 1]
    """
    n = xM_moved.size
    x_new_list = []
    y_new_list = []

    conds = np.zeros(n, dtype=float)
    used_fallback = np.zeros(n, dtype=bool)
    s_vals = np.zeros(n, dtype=float)
    t_vals = np.zeros(n, dtype=float)

    # 3) for each adjacent pair compute intersection of lines along tangents
    # Parametri aggiuntivi locali (regolabili)
    # --- Nuovo ciclo di intersezione con controllo cuspidi e fallback su lati "prima" e "dopo" ---
    miter_factor = 4.0
    max_ray_factor = 10.0
    clamp_factor = 0.4

    x_new_list = []
    y_new_list = []
    conds = np.zeros(n, dtype=float)
    used_fallback = np.zeros(n, dtype=bool)
    s_vals = np.zeros(n, dtype=float)
    t_vals = np.zeros(n, dtype=float)

    for i in range(n):
        ip1 = (i + 1) % n

        # punti e direzioni per i lati i e ip1 (moved midpoints)
        pA = np.array([xM_moved[i], yM_moved[i]])
        vA = tang[i]
        pB = np.array([xM_moved[ip1], yM_moved[ip1]])
        vB = tang[ip1]

        # calcola angolo interno tra i due spigoli (usiamo -vA rispetto a vB)
        # u = -tang[i] (verso il vertice comune), v = tang[ip1] (dal vertice in avanti)
        u = -tang[i]
        v = tang[ip1]
        cosang = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-15)
        cosang = np.clip(cosang, -1.0, 1.0)
        theta = np.arccos(cosang)  # angolo interno al vertice
        theta_half = theta * 0.5

        # calcola d_local per i e ip1 (clamp rispetto alle lunghezze locali)
        lenA = edge_len[i] if edge_len[i] > 0 else 1.0
        lenB = edge_len[ip1] if edge_len[ip1] > 0 else 1.0
        """
        d_local_A = min(d, clamp_factor * lenA)
        d_local_B = min(d, clamp_factor * lenB)
        # usa il valore più conservativo per la soglia
        d_local = min(d_local_A, d_local_B)
        """

        # se theta_half è molto piccolo, tan può esplodere; proteggi
        if theta_half < 1e-8:
            tan_half = 1e8
        else:
            tan_half = np.tan(theta_half)

        cross_product = (normals[i, 0] * normals[ip1, 1] - normals[i, 1] * normals[ip1, 0]) * z[i]

        # soglia minima richiesta per i lati adiacenti change with d_local if you want Copilot version
        Lmin = d / (tan_half + 1e-30)

        # se uno dei due lati è troppo corto rispetto alla soglia => cuspide degenerata
        cusp_degenerate = (lenA <= Lmin) or (lenB <= Lmin)

        if cross_product > 0:
            cusp_degenerate = False

        if cusp_degenerate:
            # ignora la traslazione dei due lati i e ip1:
            # effettua l'intersezione tra i lati "prima" e "dopo" quelli considerati:
            if (lenA <= Lmin) & (lenB <= Lmin):
                im = (i - 1) % n
                ip2 = (ip1 + 1) % n
            elif lenA <= Lmin:
                im = (i - 1) % n
                ip2 = ip1
            elif lenB <= Lmin:
                im = i
                ip2 = (ip1 + 1) % n
            # punti e direzioni per i lati di fallback (usiamo moved midpoints se disponibili)
            pA_fb = np.array([xM_moved[im], yM_moved[im]])
            vA_fb = tang[im]
            pB_fb = np.array([xM_moved[ip2], yM_moved[ip2]])
            vB_fb = tang[ip2]

            # se le tangenti di fallback sono quasi parallele, fallback alla media dei moved midpoints
            dot_fb = abs(np.dot(vA_fb, vB_fb) / (np.linalg.norm(vA_fb) * np.linalg.norm(vB_fb) + 1e-15))
            if dot_fb >= parallel_dot_thresh:
                pt = 0.5 * (pA_fb + pB_fb)
                used_fallback[i] = True
                conds[i] = np.inf
                s_vals[i] = np.nan;
                t_vals[i] = np.nan
            else:
                ok_fb, pt_fb, s_fb, t_fb, cond_fb = _line_intersection_from_dirs(pA_fb, vA_fb, pB_fb, vB_fb)
                conds[i] = cond_fb if np.isfinite(cond_fb) else np.inf
                if ok_fb and np.isfinite(s_fb) and np.isfinite(t_fb):
                    # accetta l'intersezione di fallback se ragionevole (non troppo lontana)
                    distA_fb = np.hypot(*(pt_fb - pA_fb))
                    distB_fb = np.hypot(*(pt_fb - pB_fb))
                    max_miter_fb = miter_factor * min(edge_len[im], edge_len[ip2])
                    if (distA_fb <= max_miter_fb and distB_fb <= max_miter_fb) or (s_fb >= 0 and t_fb >= 0):
                        pt = pt_fb
                        used_fallback[i] = False
                        s_vals[i] = s_fb;
                        t_vals[i] = t_fb
                    else:
                        pt = 0.5 * (pA_fb + pB_fb)
                        used_fallback[i] = True
                        s_vals[i] = s_fb;
                        t_vals[i] = t_fb
                else:
                    pt = 0.5 * (pA_fb + pB_fb)
                    used_fallback[i] = True
                    s_vals[i] = s_fb if 's_fb' in locals() else np.nan
                    t_vals[i] = t_fb if 't_fb' in locals() else np.nan

            x_new_list.append(pt[0]);
            y_new_list.append(pt[1])
            # continua al prossimo i
            continue

        # --- caso normale: intersezione tra le tangenti dei moved midpoints i e ip1 ---
        # fallback immediato se tangenti quasi parallele
        dot = abs(np.dot(vA, vB) / (np.linalg.norm(vA) * np.linalg.norm(vB) + 1e-15))
        if dot >= parallel_dot_thresh:
            pt = 0.5 * (pA + pB)
            x_new_list.append(pt[0]);
            y_new_list.append(pt[1])
            conds[i] = np.inf
            used_fallback[i] = True
            s_vals[i] = np.nan;
            t_vals[i] = np.nan
            continue

        ok, pt, s, t, cond = _line_intersection_from_dirs(pA, vA, pB, vB)
        conds[i] = cond if np.isfinite(cond) else np.inf

        # limiti basati sulle lunghezze degli spigoli adiacenti
        max_miter = miter_factor * min(lenA, lenB)
        max_ray = max_ray_factor * min(lenA, lenB)

        valid = False
        if ok and np.isfinite(s) and np.isfinite(t):
            distA = np.hypot(*(pt - pA))
            distB = np.hypot(*(pt - pB))
            if (s >= min_param and t >= min_param) and (distA <= max_miter and distB <= max_miter):
                valid = True
            else:
                if (s >= 0.0 and t >= 0.0) and (distA <= max_ray and distB <= max_ray):
                    valid = True

        if not valid:
            """
            rAB = 0.5 * (pB - pA)
            rAB_mod = np.hypot(rAB[0], rAB[1])
            tAB_mod = - (rAB_mod**2) / (rAB[0] * abs(vA[0]) - rAB[1] * abs(vA[1]))
            pt = pA + tAB_mod * vA
            """
            """
            pt = 0.5 * (pA + pB)
            r_pt = np.hypot(pt[0], pt[1])
            pt = pt * (1 + 0.5* d / r_pt)
            """
            if cross_product > 1e-12:
                pt = np.array([x[ip1], y[ip1]])
                pt = pt + normals[i, :] * d
                x_new_list.append(pt[0]);
                y_new_list.append(pt[1])
                pt = np.array([x[ip1], y[ip1]])
                pt = pt + normals[ip1, :] * d
            else:
                pt = 0.5 * (pB + pA)

            used_fallback[i] = True
        else:
            used_fallback[i] = False

        x_new_list.append(pt[0]);
        y_new_list.append(pt[1])
        s_vals[i] = s if s is not None else np.nan
        t_vals[i] = t if t is not None else np.nan

    x_new = np.asarray(x_new_list, dtype=float)
    y_new = np.asarray(y_new_list, dtype=float)

    # 4) cleanup: remove near-duplicates and simple collinearities
    x_new, y_new = remove_close_vertices(x_new, y_new, tol=close_tol)
    x_new, y_new = remove_collinear_simple(x_new, y_new, tol=close_tol)

    # 5) final safety: if result self-intersects badly, fallback to conservative midpoint shrink
    def _has_self_intersection_local(xx, yy):
        m = xx.size
        if m < 4:
            return False
        pts = np.column_stack((xx, yy))
        for a in range(m):
            A = pts[a];
            B = pts[(a + 1) % m]
            for b in range(a + 2, m):
                if (b + 1) % m == a:
                    continue
                C = pts[b];
                D = pts[(b + 1) % m]

                # simple segment intersection test
                def orient(ax, ay, bx, by, cx, cy):
                    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)

                o1 = orient(A[0], A[1], B[0], B[1], C[0], C[1])
                o2 = orient(A[0], A[1], B[0], B[1], D[0], D[1])
                o3 = orient(C[0], C[1], D[0], D[1], A[0], A[1])
                o4 = orient(C[0], C[1], D[0], D[1], B[0], B[1])
                if o1 * o2 < 0 and o3 * o4 < 0:
                    return True
        return False

    if _has_self_intersection_local(x_new, y_new):
        # conservative fallback: shrink midpoints toward polygon centroid by factor 0.5 and recompute intersections
        cx = np.mean(x);
        cy = np.mean(y)
        xM_shrunk = 0.5 * (xM + np.array([cx] * n))
        yM_shrunk = 0.5 * (yM + np.array([cy] * n))
        xM_moved = xM_shrunk + d * normals[:, 0]
        yM_moved = yM_shrunk + d * normals[:, 1]
        x_new_list = [];
        y_new_list = []
        for i in range(n):
            ip1 = (i + 1) % n
            pA = np.array([xM_moved[i], yM_moved[i]])
            vA = tang[i]
            pB = np.array([xM_moved[ip1], yM_moved[ip1]])
            vB = tang[ip1]
            ok, pt, s, t, cond = _line_intersection_from_dirs(pA, vA, pB, vB)
            if not ok:
                pt = 0.5 * (pA + pB)
            x_new_list.append(pt[0]);
            y_new_list.append(pt[1])
        x_new = np.asarray(x_new_list);
        y_new = np.asarray(y_new_list)
        x_new, y_new = remove_close_vertices(x_new, y_new, tol=close_tol)
        x_new, y_new = remove_collinear_simple(x_new, y_new, tol=close_tol)

    # diagnostics
    info["midpoints"] = np.column_stack((xM, yM))
    info["moved_midpoints"] = np.column_stack((xM_moved, yM_moved))
    info["tangents"] = tang
    info["conds"] = conds
    info["used_fallback"] = used_fallback
    info["s_vals"] = s_vals
    info["t_vals"] = t_vals

    return x_new, y_new

def burn_surface_circular(x, y, z, regression_rate, dt,
                          min_param=1e-9, parallel_dot_thresh=0.9999,
                          close_tol=1e-12, merge_tol=1e-9):
    """
    Trasla i midpoint dei lati e trova le intersezioni tramite le tangenti.
    Individua i punti allo stesso raggio e considera archi di cerchio nel mezzo. In caso di fallback
    nell'intersezione dei punti medi, si trasla solo l'arco di circonferenza per assicurare robustezza.
    - x,y: contorno (1D arrays, ordine poligono)
    - z: +1/-1 per orientazione normale (normale = rotate tangente by +90 * z)
    - regression_rate, dt -> d = regression_rate * dt
    Returns: x_new, y_new
    info contains diagnostics: conds, fallbacks, midpoints, moved_midpoints
    """
    info = {}
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()

    # 0) cleanup duplicates
    x, y = remove_close_vertices(x, y, tol=close_tol)
    x, y = remove_collinear_simple(x, y, tol=close_tol)
    x, y = remove_samearc_simple(x, y, tol=close_tol)

    if x.size > 2:
        # 1) compute edges and midpoints
        x2 = np.r_[x, x[0]];
        y2 = np.r_[y, y[0]]

        rads = np.hypot(x, y)
        rads2 = np.hypot(x2, y2)

        dx = np.diff(x2);
        dy = np.diff(y2)
        edge_len = np.hypot(dx, dy)
        # protect division
        edge_len_safe = edge_len.copy()
        edge_len_safe[edge_len_safe == 0] = 1.0

        # tangents unitari (da vertice i a i+1)
        tx = dx / edge_len_safe
        ty = dy / edge_len_safe
        tang = np.column_stack((tx, ty))

        mask_same_rad = np.zeros_like(x, dtype=bool)
        for i in range(x.size):
            if np.isclose(rads2[i], rads2[i + 1], atol=close_tol):
                mask_same_rad[i] = True

        # midpoints dei lati
        xM = 0.5 * (x2[:-1] + x2[1:])
        yM = 0.5 * (y2[:-1] + y2[1:])

        # --- assicurati che z sia per-edge ---
        z = np.asarray(z).ravel()
        if z.size == 1:
            z = np.ones(xM.shape[0], dtype=float) * z[0]
        elif z.size != xM.shape[0]:
            # se z è per-vertice, converti a per-edge (es. take z at edge start)
            if z.size == x.size:
                z = z  # se vuoi usare per-vertex, mappa opportunamente
            else:
                z = np.resize(z, xM.shape[0])

        # normals (rotate tangenti +90 deg) e applica z
        normals = np.column_stack((ty * z, -tx * z))
        # normalizza normals per sicurezza e gestisci edge quasi nulli
        n_norm = np.hypot(normals[:, 0], normals[:, 1])
        small_edge_mask = (edge_len < 1e-12)
        n_norm[n_norm == 0] = 1.0
        normals[:, 0] /= n_norm
        normals[:, 1] /= n_norm

    else:
        try:
            xM = x[0]
            yM = y[0]
        except IndexError:
            xM = x
            yM = y

        mask_same_rad = np.ones_like(xM, dtype=bool)
        normals = np.array([(xM / np.hypot(xM, yM)), (yM / np.hypot(xM, yM))])
        tang = np.array([(- yM * z / np.hypot(xM, yM)), (xM * z / np.hypot(xM, yM))])

    # forza direzione verso l'esterno usando il centroide
    """
    cx = np.mean(x)
    cy = np.mean(y)
    centroid = np.array([cx, cy])
    for i_edge in range(normals.shape[0]):
        mid = np.array([xM[i_edge], yM[i_edge]])
        if np.dot(mid - centroid, normals[i_edge]) < 0:
            normals[i_edge] *= -1.0
    """

    # 2) move midpoints along normals con clamp locale
    d = float(regression_rate) * float(dt)
    # clamp factor: frazione della lunghezza minima degli spigoli adiacenti
    clamp_factor = 0.4
    xM_moved = np.empty_like(xM)
    yM_moved = np.empty_like(yM)
    try:
        xM_moved = xM + d * normals[:, 0]
        yM_moved = yM + d * normals[:, 1]
    except:
        xM_moved = xM + d * normals[0]
        yM_moved = yM + d * normals[1]
    """
    for i_edge in range(xM.size):
        # calcola una d locale basata sulla lunghezza dell'edge
        local_len = edge_len[i_edge] if edge_len[i_edge] > 0 else 1.0
        d_local = min(d, clamp_factor * local_len)

        # se edge troppo corto, evita spostamento e segnala
        if small_edge_mask[i_edge]:
            xM_moved[i_edge] = xM[i_edge]
            yM_moved[i_edge] = yM[i_edge]
        else:
            xM_moved[i_edge] = xM[i_edge] + d_local * normals[i_edge, 0]
            yM_moved[i_edge] = yM[i_edge] + d_local * normals[i_edge, 1]
    """
    n = np.asarray(xM_moved).size
    x_new_list = []
    y_new_list = []

    conds = np.zeros(n, dtype=float)
    used_fallback = np.zeros(n, dtype=bool)
    s_vals = np.zeros(n, dtype=float)
    t_vals = np.zeros(n, dtype=float)

    # 3) for each adjacent pair compute intersection of lines along tangents
    # Parametri aggiuntivi locali (regolabili)
    # --- Nuovo ciclo di intersezione con controllo cuspidi e fallback su lati "prima" e "dopo" ---
    miter_factor = 4.0
    max_ray_factor = 10.0
    clamp_factor = 0.4

    x_new_list = []
    y_new_list = []
    conds = np.zeros(n, dtype=float)
    used_fallback = np.zeros(n, dtype=bool)
    s_vals = np.zeros(n, dtype=float)
    t_vals = np.zeros(n, dtype=float)

    for i in range(n):

        if n > 2:
            ip1 = (i + 1) % n
        else:
            x_new_list.append(xM_moved);
            y_new_list.append(yM_moved)
            continue

        # punti e direzioni per i lati i e ip1 (moved midpoints)
        pA = np.array([xM_moved[i], yM_moved[i]])
        vA = tang[i]
        pB = np.array([xM_moved[ip1], yM_moved[ip1]])
        vB = tang[ip1]

        # calcola angolo interno tra i due spigoli (usiamo -vA rispetto a vB)
        # u = -tang[i] (verso il vertice comune), v = tang[ip1] (dal vertice in avanti)
        u = -tang[i]
        v = tang[ip1]
        cosang = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-15)
        cosang = np.clip(cosang, -1.0, 1.0)
        theta = np.arccos(cosang)  # angolo interno al vertice
        theta_half = theta * 0.5

        # calcola d_local per i e ip1 (clamp rispetto alle lunghezze locali)
        lenA = edge_len[i] if edge_len[i] > 0 else 1.0
        lenB = edge_len[ip1] if edge_len[ip1] > 0 else 1.0
        """
        d_local_A = min(d, clamp_factor * lenA)
        d_local_B = min(d, clamp_factor * lenB)
        # usa il valore più conservativo per la soglia
        d_local = min(d_local_A, d_local_B)
        """

        # se theta_half è molto piccolo, tan può esplodere; proteggi
        if theta_half < 1e-8:
            tan_half = 1e8
        else:
            tan_half = np.tan(theta_half)

        cross_product = (normals[i, 0] * normals[ip1, 1] - normals[i, 1] * normals[ip1, 0]) * z[i]

        # soglia minima richiesta per i lati adiacenti change with d_local if you want Copilot version
        Lmin = d / (tan_half + 1e-30)

        # se uno dei due lati è troppo corto rispetto alla soglia => cuspide degenerata
        cusp_degenerate = (lenA <= Lmin) or (lenB <= Lmin)

        if cross_product > 0:
            cusp_degenerate = False

        if cusp_degenerate:
            # ignora la traslazione dei due lati i e ip1:
            # effettua l'intersezione tra i lati "prima" e "dopo" quelli considerati:
            if (lenA <= Lmin) & (lenB <= Lmin):
                im = (i - 1) % n
                ip2 = (ip1 + 1) % n
            elif lenA <= Lmin:
                im = (i - 1) % n
                ip2 = ip1
            elif lenB <= Lmin:
                im = i
                ip2 = (ip1 + 1) % n

            # punti e direzioni per i lati di fallback (usiamo moved midpoints se disponibili)
            pA_fb = np.array([xM_moved[im], yM_moved[im]])
            vA_fb = tang[im]
            pB_fb = np.array([xM_moved[ip2], yM_moved[ip2]])
            vB_fb = tang[ip2]

            # se le tangenti di fallback sono quasi parallele, fallback alla media dei moved midpoints
            dot_fb = abs(np.dot(vA_fb, vB_fb) / (np.linalg.norm(vA_fb) * np.linalg.norm(vB_fb) + 1e-15))
            if dot_fb >= parallel_dot_thresh:
                pt = 0.5 * (pA_fb + pB_fb)
                used_fallback[i] = True
                conds[i] = np.inf
                s_vals[i] = np.nan;
                t_vals[i] = np.nan
            else:
                ok_fb, pt_fb, s_fb, t_fb, cond_fb = _line_intersection_from_dirs(pA_fb, vA_fb, pB_fb, vB_fb)
                conds[i] = cond_fb if np.isfinite(cond_fb) else np.inf
                if ok_fb and np.isfinite(s_fb) and np.isfinite(t_fb):
                    # accetta l'intersezione di fallback se ragionevole (non troppo lontana)
                    distA_fb = np.hypot(*(pt_fb - pA_fb))
                    distB_fb = np.hypot(*(pt_fb - pB_fb))
                    max_miter_fb = miter_factor * min(edge_len[im], edge_len[ip2])
                    if (distA_fb <= max_miter_fb and distB_fb <= max_miter_fb) or (s_fb >= 0 and t_fb >= 0):
                        pt = pt_fb
                        used_fallback[i] = False
                        s_vals[i] = s_fb;
                        t_vals[i] = t_fb
                    else:
                        pt = 0.5 * (pA_fb + pB_fb)
                        used_fallback[i] = True
                        s_vals[i] = s_fb;
                        t_vals[i] = t_fb
                else:
                    pt = 0.5 * (pA_fb + pB_fb)
                    used_fallback[i] = True
                    s_vals[i] = s_fb if 's_fb' in locals() else np.nan
                    t_vals[i] = t_fb if 't_fb' in locals() else np.nan

            x_new_list.append(pt[0]);
            y_new_list.append(pt[1])
            # continua al prossimo i
            continue

        # --- caso normale: intersezione tra le tangenti dei moved midpoints i e ip1 ---
        # fallback immediato se tangenti quasi parallele
        dot = abs(np.dot(vA, vB) / (np.linalg.norm(vA) * np.linalg.norm(vB) + 1e-15))
        if dot >= parallel_dot_thresh:
            pt = 0.5 * (pA + pB)
            x_new_list.append(pt[0]);
            y_new_list.append(pt[1])
            conds[i] = np.inf
            used_fallback[i] = True
            s_vals[i] = np.nan;
            t_vals[i] = np.nan
            continue

        ok, pt, s, t, cond = _line_intersection_from_dirs(pA, vA, pB, vB)
        conds[i] = cond if np.isfinite(cond) else np.inf

        # limiti basati sulle lunghezze degli spigoli adiacenti
        max_miter = miter_factor * min(lenA, lenB)
        max_ray = max_ray_factor * min(lenA, lenB)

        valid = False
        if ok and np.isfinite(s) and np.isfinite(t):
            distA = np.hypot(*(pt - pA))
            distB = np.hypot(*(pt - pB))
            if (s >= min_param and t >= min_param) and (distA <= max_miter and distB <= max_miter):
                valid = True
            else:
                if (s >= 0.0 and t >= 0.0) and (distA <= max_ray and distB <= max_ray):
                    valid = True

        if not valid:
            """
            rAB = 0.5 * (pB - pA)
            rAB_mod = np.hypot(rAB[0], rAB[1])
            tAB_mod = - (rAB_mod**2) / (rAB[0] * abs(vA[0]) - rAB[1] * abs(vA[1]))
            pt = pA + tAB_mod * vA
            """
            """
            pt = 0.5 * (pA + pB)
            r_pt = np.hypot(pt[0], pt[1])
            pt = pt * (1 + 0.5* d / r_pt)
            """
            if cross_product > 1e-12:
                if mask_same_rad[i]:
                    pt = np.array([x[ip1], y[ip1]])
                    pt = pt + normals[i, :] * d
                elif mask_same_rad[ip1]:
                    pt = np.array([x[ip1], y[ip1]])
                    pt = pt + normals[ip1, :] * d
                else:
                    pt = np.array([x[ip1], y[ip1]])
                    pt = pt + normals[i, :] * d
                    x_new_list.append(pt[0]);
                    y_new_list.append(pt[1])
                    pt = np.array([x[ip1], y[ip1]])
                    pt = pt + normals[ip1, :] * d
            else:
                pt = 0.5 * (pB + pA)

            used_fallback[i] = True
        else:
            used_fallback[i] = False

        x_new_list.append(pt[0]);
        y_new_list.append(pt[1])
        s_vals[i] = s if s is not None else np.nan
        t_vals[i] = t if t is not None else np.nan

    x_new = np.asarray(x_new_list, dtype=float)
    y_new = np.asarray(y_new_list, dtype=float)

    # 4) cleanup: remove near-duplicates and simple collinearities
    x_new, y_new = remove_close_vertices(x_new, y_new, tol=close_tol)
    x_new, y_new = remove_collinear_simple(x_new, y_new, tol=close_tol)

    # 5) final safety: if result self-intersects badly, fallback to conservative midpoint shrink
    def _has_self_intersection_local(xx, yy):
        m = xx.size
        if m < 4:
            return False
        pts = np.column_stack((xx, yy))
        for a in range(m):
            A = pts[a];
            B = pts[(a + 1) % m]
            for b in range(a + 2, m):
                if (b + 1) % m == a:
                    continue
                C = pts[b];
                D = pts[(b + 1) % m]

                # simple segment intersection test
                def orient(ax, ay, bx, by, cx, cy):
                    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)

                o1 = orient(A[0], A[1], B[0], B[1], C[0], C[1])
                o2 = orient(A[0], A[1], B[0], B[1], D[0], D[1])
                o3 = orient(C[0], C[1], D[0], D[1], A[0], A[1])
                o4 = orient(C[0], C[1], D[0], D[1], B[0], B[1])
                if o1 * o2 < 0 and o3 * o4 < 0:
                    return True
        return False

    if _has_self_intersection_local(x_new, y_new):
        # conservative fallback: shrink midpoints toward polygon centroid by factor 0.5 and recompute intersections
        cx = np.mean(x);
        cy = np.mean(y)
        xM_shrunk = 0.5 * (xM + np.array([cx] * n))
        yM_shrunk = 0.5 * (yM + np.array([cy] * n))
        xM_moved = xM_shrunk + d * normals[:, 0]
        yM_moved = yM_shrunk + d * normals[:, 1]
        x_new_list = [];
        y_new_list = []
        for i in range(n):
            ip1 = (i + 1) % n
            pA = np.array([xM_moved[i], yM_moved[i]])
            vA = tang[i]
            pB = np.array([xM_moved[ip1], yM_moved[ip1]])
            vB = tang[ip1]
            ok, pt, s, t, cond = _line_intersection_from_dirs(pA, vA, pB, vB)
            if not ok:
                pt = 0.5 * (pA + pB)
            x_new_list.append(pt[0]);
            y_new_list.append(pt[1])
        x_new = np.asarray(x_new_list);
        y_new = np.asarray(y_new_list)
        x_new, y_new = remove_close_vertices(x_new, y_new, tol=close_tol)
        x_new, y_new = remove_collinear_simple(x_new, y_new, tol=close_tol)

    # diagnostics
    info["midpoints"] = np.column_stack((xM, yM))
    info["moved_midpoints"] = np.column_stack((xM_moved, yM_moved))
    info["tangents"] = tang
    info["conds"] = conds
    info["used_fallback"] = used_fallback
    info["s_vals"] = s_vals
    info["t_vals"] = t_vals

    return x_new, y_new

def burn_grain(x, y, z, regression_rate, dt, circular=False,
                    min_param=1e-9, parallel_dot_thresh=0.9999,
                    close_tol=1e-12, merge_tol=1e-9):
    """
    Helper function for main mission script.
    :param x:
    :param y:
    :param z:
    :param regression_rate:
    :param dt:
    :param circular:
    :param min_param:
    :param parallel_dot_thresh:
    :param close_tol:
    :param merge_tol:
    :return:
    """
    if circular:
        x_out, y_out = burn_surface_circular(x, y, z, regression_rate, dt,
                          min_param, parallel_dot_thresh,
                          close_tol, merge_tol)
    else:
        x_out, y_out = burn_surface(x, y, z, regression_rate, dt,
                     min_param, parallel_dot_thresh,
                     close_tol, merge_tol)
    return x_out, y_out

if __name__ == "__main__":
    # lc = 2  # lunghezza del grano [m]
    radius = 8
    step = 26.336  # passo elica [m]
    lc = step
    n_points_per_side = 100
    n_sides = 4

    # ---- Test 1: poligono semplice ----
    x_sq, y_sq = geomcalc.create_regular_poligon(n_sides, radius)
    # mischio gli indici per simulare input disordinato
    perm = np.random.permutation(len(x_sq))
    x_sq_shuffled = x_sq[perm]
    y_sq_shuffled = y_sq[perm]

    print(f"==== TEST 1: Poligono (lato={n_sides}) ====")

    # trasla e ordina
    x_t, y_t = geomcalc.translate_figure(x_sq_shuffled, y_sq_shuffled)
    x_s, y_s = geomcalc.sort_input(x_t, y_t)

    x_f, y_f = geomcalc.fill_borders(x_s, y_s, n_points_per_side)
    x_f2, y_f2 = burn_surface(x_f, y_f, 1, 0.5, 1)

    plt.figure()
    plt.plot(x_f, y_f, 'b')
    plt.plot(x_f2, y_f2, 'r', label='burned')

    for times in range(100):
        x_f2, y_f2 = burn_surface(x_f2, y_f2, 1, 0.5, 1)
        plt.plot(x_f2, y_f2, 'r')

    plt.show()

    # calcolo superfici
    port_area, burning_area = geomcalc.calculate_surfaces_from_points(x_f, y_f, lc)
    print(f"Poligono: PortArea = {port_area:.6f} m^2 ; BurningArea (step=0) = {burning_area:.6f} m^2")
    # atteso: PortArea ~ 4 (area quadrato lato 2), ma nota: funzione somma aree triangoli con origine -> area effettiva interna
    # per quadrato centrato l'area dovrebbe essere 4.0

    port_area4, burning_area4 = geomcalc.calculate_surfaces_from_points(x_f, y_f, lc, step)
    print(f"Poligono: PortArea = {port_area4:.6f} m^2 ; BurningArea (step={step:.3f}) = {burning_area4:.6f} m^2")

    # ---- Test 2: poligono irregolare (approssimazione cerchio) ----
    theta = np.linspace(0, 2 * np.pi, 50, endpoint=False)
    r = 1.0 + 0.2 * np.cos(10 * theta)  # forma non convessa ma chiusa
    x_poly = (r * np.cos(theta))  # traslato per test translate
    y_poly = (r * np.sin(theta))

    print("\n==== TEST 2: Poligono irregolare ====")

    # x_t2, y_t2 = translate_figure(x_poly, y_poly)
    # x_s2, y_s2 = sort_input(x_t2, y_t2)
    x_s2, y_s2 = geomcalc.sort_input(x_poly, y_poly)

    plt.figure()
    plt.plot(x_s2, y_s2, 'b', label='original')

    x_s2b, y_s2b = burn_surface_circular(x_s2, y_s2, 1, 0.05, 1)
    plt.plot(x_s2b, y_s2b, 'r')

    for crazy_time in range(100):
        for times in range(3):
            x_s2b, y_s2b = burn_surface_circular(x_s2b, y_s2b, 1, 0.05, 1)
            if crazy_time % 20 == 0:
                plt.plot(x_s2b, y_s2b, ['g', 'y', 'k'][times])

    for times in range(0):
        x_s2b, y_s2b = burn_surface(x_s2b, y_s2b, 1, 0.05, 1)
        plt.plot(x_s2b, y_s2b, ['g', 'y', 'k'][times])

    plt.legend()
    plt.show()

    """
    port_area2, burning_area2 = calculate_surfaces_from_points(x_s2, y_s2, lc)
    print(f"Poligono: PortArea = {port_area2:.6f} m^2 ; BurningArea (step=0) = {burning_area2:.6f} m^2")

    # ---- Test 3: burning area with step > 0 (esempio) ----

    port_area3, burning_area3 = calculate_surfaces_from_points(x_s2, y_s2, lc, step)
    print(f"Poligono (step={step} m): PortArea = {port_area3:.6f} m^2 ; BurningArea (step={step:.3f}) = {burning_area3:.6f} m^2")

    # ---- Quick numeric checks: confronto area con shoelace ----
    def shoelace_area(x, y):
        x = np.asarray(x)
        y = np.asarray(y)
        x2 = np.r_[x, x[0]]
        y2 = np.r_[y, y[0]]
        return 0.5 * np.abs(np.sum(x2[:-1] * y2[1:] - x2[1:] * y2[:-1]))


    area_shoelace_sq = shoelace_area(x_s, y_s)
    area_shoelace_poly = shoelace_area(x_s2, y_s2)
    print("\nConfronti con shoelace:")
    print(f"Poligono regolare: PortArea (triangles) = {port_area:.6f}, Shoelace = {area_shoelace_sq:.6f}")
    print(f"Poligono irregolare: PortArea (triangles) = {port_area2:.6f}, Shoelace = {area_shoelace_poly:.6f}")
    """

    """
    plot_polygon(x_sq_shuffled, y_sq_shuffled, title='Quadrato (shuffled input)')
    plot_polygon(x_s, y_s, title='Quadrato (translated + sorted CCW)')
    plot_polygon(x_f, y_f, title='Quadrato (filled borders)')
    plot_polygon(x_poly, y_poly, title='Poligono irregolare (input)')
    plot_polygon(x_s2, y_s2, title='Poligono irregolare (translated + sorted CCW)')
    """

    """
    # Assert ragionevoli (tolleranza)
    tol = 1e-6
    assert abs(port_area - area_shoelace_sq) < 1e-8 or abs(port_area - area_shoelace_sq) / max(area_shoelace_sq,
                                                                                               1e-12) < 1e-6, "PortArea mismatch for square"
    assert abs(port_area2 - area_shoelace_poly) < 1e-6 or abs(port_area2 - area_shoelace_poly) / max(area_shoelace_poly,
                                                                                                     1e-12) < 1e-6, "PortArea mismatch for polygon"

    print("\nTutti i test completati con successo.")
    """

    """
    x_inst = np.array([2.0, 2.0, 0.0])
    y_inst = np.array([0.0, 2.0, 2.0])
    x_rep, y_rep = create_repeated_instance(x_inst, y_inst, 2)
    plot_polygon(x_rep, y_rep, title='Poligono ripetuto')
    x_fillc, y_fillc = fill_borders_circumference(x_rep, y_rep, 50)
    plot_polygon(x_fillc, y_fillc, title='Poligono ripetuto')

    x_bc, y_bc = burn_surface_circular(x_fillc, y_fillc, 1, 0.05, 1)
    x_bfc, y_bfc = fill_borders_circumference(x_bc, y_bc, 50)

    plt.figure()
    plt.plot(x_fillc, y_fillc, 'b')
    plt.plot(x_bfc, y_bfc)

    for times in range(500):
        x_bc, y_bc = burn_surface_circular(x_bc, y_bc, 1, 0.05, 1)
        x_bfc, y_bfc = fill_borders_circumference(x_bc, y_bc, 50)
        if times % 20 == 0:
            plt.plot(x_bfc, y_bfc)

    plt.show()
    """
# end of file