# import IPython.display as display
from pathlib import Path

import tensorflow as tf

from dreamify.lib import TiledGradients, validate_dream_params
from dreamify.utils import (
    deprocess_image,
    get_image,
    preprocess_image,
    save_output,
    show,
)
from dreamify.utils.configure import Config


@validate_dream_params
def deepdream(
    image_path,
    output_path="dream.png",
    iterations=100,
    learning_rate=0.01,
    octaves=range(-2, 3),
    octave_scale=1.3,
    save_video=False,
    save_gif=False,
    duration=3,
    mirror_video=False,
):
    output_path = Path(output_path)

    base_model = tf.keras.applications.InceptionV3(
        include_top=False, weights="imagenet"
    )

    names = ["mixed3", "mixed5"]
    layers = [base_model.get_layer(name).output for name in names]

    ft_ext = tf.keras.Model(inputs=base_model.input, outputs=layers)
    get_tiled_gradients = TiledGradients(ft_ext)

    dream_model = tf.keras.Model(inputs=base_model.input, outputs=layers)

    img = get_image(image_path)
    img = preprocess_image(img)

    original_shape = img.shape[1:-1]

    config = Config(
        feature_extractor=dream_model,
        layer_settings=layers,
        original_shape=original_shape,
        save_video=save_video,
        save_gif=save_gif,
        enable_framing=True,
        duration=duration,
        mirror_video=mirror_video,
        max_frames_to_sample=iterations * len(octaves),
    )

    for octave in octaves:
        new_size = tf.cast(tf.convert_to_tensor(original_shape), tf.float32) * (
            octave_scale**octave
        )
        new_size = tf.cast(new_size, tf.int32)
        img = tf.image.resize(img, tf.cast(new_size, tf.int32))

        for iteration in range(iterations):
            gradients = get_tiled_gradients(tf.squeeze(img), new_size)
            img = img + gradients * learning_rate
            img = tf.clip_by_value(img, -1, 1)

            if iteration % 10 == 0:
                # display.clear_output(wait=True)
                show(deprocess_image(img))
                print("Octave {}, Iteration {}".format(octave, iteration))

            if config.enable_framing and config.framer.continue_framing():
                config.framer.add_to_frames(img)

    img = deprocess_image(img)
    show(img)

    save_output(img, output_path, config)

    return img


def main(img_path, save_video=False, save_gif=False, duration=3, mirror_video=False):
    if img_path is None:
        img_path = (
            "https://storage.googleapis.com/download.tensorflow.org/"
            "example_images/YellowLabradorLooking_new.jpg"
        )

    deepdream(
        image_path=img_path,
        save_video=save_video,
        save_gif=save_gif,
        duration=duration,
        mirror_video=mirror_video,
    )


if __name__ == "__main__":
    main()
