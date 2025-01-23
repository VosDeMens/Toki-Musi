from collections.abc import Callable
import numpy as np
from my_types import floatlist
from scipy.special import expit  # type: ignore


def fits_shape(x: floatlist, f: Callable[[int], floatlist]) -> float:
    x_centered = x - np.mean(x)

    n = len(x)
    mask = f(n)
    mask -= np.mean(mask)

    # pair_wise = x_centered * mask
    dot_product = np.dot(x_centered, mask)
    cos_angle = dot_product / np.linalg.norm(mask) / np.linalg.norm(x_centered)

    # print(f"f = {str(f).split(" ")[1]}")
    # print(f"x_centered = {x_centered}")
    # print(f"mask =       {mask}")
    # print(f"pair_wise =  {pair_wise}")
    # print(f"{dot_product = }")
    # print(f"{cos_angle = }")

    return cos_angle


def center_and_normalise(x: floatlist) -> floatlist:
    centered = x - np.mean(x)
    and_normalised = centered / np.linalg.norm(centered)
    return and_normalised


def step(n: int) -> floatlist:
    return expit(np.linspace(-10, 10, n))


def step_sloppy(n: int) -> floatlist:
    return expit(np.linspace(-4, 4, n))


def step_left(n: int) -> floatlist:
    t_q = int(n * 3 / 4)
    return np.concatenate((expit(np.linspace(-10, 10, t_q)), np.ones(n - t_q)))


def step_right(n: int) -> floatlist:
    t_q = int(n * 3 / 4)
    return np.concatenate((np.zeros(n - t_q), expit(np.linspace(-10, 10, t_q))))


def double_step(n: int) -> floatlist:
    return expit(np.linspace(-25, 10, n)) + expit(np.linspace(-10, 25, n))


def double_step_sloppy(n: int) -> floatlist:
    return expit(np.linspace(-12, 4, n)) + expit(np.linspace(-4, 12, n))


def double_step_left(n: int) -> floatlist:
    t_q = int(n * 3 / 4)
    return np.concatenate(
        (
            expit(np.linspace(-25, 10, t_q)) + expit(np.linspace(-10, 25, t_q)),
            2 * np.ones(n - t_q),
        )
    )


def double_step_right(n: int) -> floatlist:
    t_q = int(n * 3 / 4)
    return np.concatenate(
        (
            np.zeros(n - t_q),
            expit(np.linspace(-25, 10, t_q)) + expit(np.linspace(-10, 25, t_q)),
        )
    )


def linear(n: int) -> floatlist:
    return np.linspace(0, 1, n, dtype=float)


def flat_then_linear(n: int) -> floatlist:
    return np.concatenate(
        (np.zeros(int(n / 2)), np.linspace(0, 1, int(np.ceil(n / 2))))
    )


def bell(n: int) -> floatlist:
    input_values = np.linspace(-2, 2, n)
    return np.e ** -(input_values**2)


shape_dict = {
    "step": step,
    "step 2": step_sloppy,
    "step l": step_left,
    "step r": step_right,
    "double": double_step,
    "double 2": double_step_sloppy,
    "double l": double_step_left,
    "double r": double_step_right,
    "linear": linear,
    "flat_linear": flat_then_linear,
    "bell": bell,
}


def get_all_masks(n: int):
    return [f(n) for f in shape_dict.values()]


if __name__ == "__main__":
    x = -np.array([2, 2, 5, 5, 2, 2], dtype=float)

    print(fits_shape(x, step))
    print(fits_shape(x, linear))
    print(fits_shape(x, bell))

    print(bell(16))
