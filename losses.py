import tensorflow as tf
from ops import *

def clip_tensor(tens):
    return tens
    tf.print(tens)
    mask = tf.equal(tens, 1e-42 * tf.ones_like(tens))
    new_tensor = tf.multiply(tens, tf.cast(mask, 'float32'))
    return new_tensor
    #return tf.clip_by_value(tens,1e-10,1)


def CAN_loss(model):
    #builds optimizers and losses

    model.G                  = model.generator(model, model.z)
    model.D, model.D_logits, summaries_d     = model.discriminator(model,
                                                              model.inputs, reuse=False)
    if model.experience_flag:
      try:
        model.experience_selection = tf.convert_to_tensor(random.sample(model.experience_buffer, 16))
      except ValueError:
        model.experience_selection = tf.convert_to_tensor(model.experience_buffer)
      model.G = tf.concat([model.G, model.experience_selection], axis=0)

    model.D_, model.D_logits_, summaries_d_ = model.discriminator(model,
                                                              model.G, reuse=True)
    model.d_sum = histogram_summary("d", model.D)
    model.d__sum = histogram_summary("d_", model.D_)
    model.G_sum = image_summary("G", model.G)
    model.img_sum = image_summary("Inpts", model.inputs)
    mean, variance = tf.nn.moments(model.G,axes=[1])
    grads_wrt_inpt = tf.gradients(model.D_logits, model.inputs)
    grads_wrt_gen_inpt = tf.gradients(model.D_logits_,model.G)
    model.grad_sum = image_summary('grad_wrt_inpt', grads_wrt_inpt[0])
    model.grad_gen_sum = image_summary('G_grads_inpt',grads_wrt_gen_inpt[0])
    model.grad_debug = grads_wrt_inpt
    model.mean_debug = mean
    model.variance_debug = variance
    model.img_mean = image_summary('img_mean', tf.reshape(mean,[-1,128,256,3]))
    model.img_var = image_summary('img_var', tf.reshape(variance, [-1, 128, 256, 3]))



    true_label = tf.random_uniform(tf.shape(model.D), .7, 1.2)
    false_label = tf.random_uniform(tf.shape(model.D_), 0.00, 0.3)

    disc_concat = tf.concat([model.D_logits, model.D_logits_], axis=0)
    label_concat = tf.concat([tf.ones_like(model.D),
                              tf.zeros_like(model.D_)],axis=0)
    model.label_debug = tf.ones_like(model.D)
    print(disc_concat)
    print(label_concat)
    model.label_concat = label_concat
    model.disc_concat = disc_concat

    correct_prediction = tf.equal(tf.argmax(model.disc_concat, 1), tf.argmax(model.label_concat, 1))
    model.accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))


    model.d_loss_total = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=disc_concat,
                                                                             labels=label_concat))




    model.d_loss = model.d_loss_total
    # if classifier is set, then use the classifier, o/w use the clasification layers in the discriminator

    model.g_loss_fake = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=model.D_logits_,
                                                                                 labels=tf.ones_like(model.D_)))

    model.g_loss = (model.g_loss_fake)

    model.d_loss_real_sum       = scalar_summary("d_loss_complete", model.d_loss_total)
    model.g_loss_sum = scalar_summary("g_loss", model.g_loss)
    model.d_loss_sum = scalar_summary("d_loss", model.d_loss)
    model.d_sum = merge_summary(
        [ model.d_sum, model.d_loss_real_sum,
          model.d_loss_sum])
    model.g_sum = merge_summary([model.z_sum, model.d__sum,model.img_sum,
                                 model.img_mean,model.img_var,model.grad_sum,model.grad_gen_sum,
      model.G_sum, model.g_loss_sum])

    model.g_opt = tf.train.AdamOptimizer(learning_rate=model.learning_rate, beta1=0.5)
    #grads_g = model.g_opt.compute_gradients(model.g_loss)

    grad_summ_op = None

    model.d_opt = tf.train.AdamOptimizer(learning_rate=model.learning_rate, beta1=0.5)

    t_vars = tf.trainable_variables()
    d_vars = [var for var in t_vars if 'd_' in var.name]
    g_vars = [var for var in t_vars if 'g_' in var.name]

    d_update = model.d_opt.minimize(model.d_loss, var_list=d_vars)
    g_update = model.g_opt.minimize(model.g_loss, var_list=g_vars)

    return d_update, g_update, [model.d_loss, model.g_loss], [model.d_sum, model.g_sum],grad_summ_op, model.D

def WCAN_loss(model):
    pass


def GAN_loss(model):
    model.G                  = model.generator(model.z, model.y)
    model.D, model.D_logits   = model.discriminator(model.inputs, model.y, reuse=False)
    model.D_, model.D_logits_ = model.discriminator(model.G, model.y, reuse=True)

    true_label = tf.random_uniform(tf.shape(model.D),.8, 1.2)
    false_label = tf.random_uniform(tf.shape(model.D_), 0.0, 0.3)

    model.d_loss_real = tf.reduce_mean(
      sigmoid_cross_entropy_with_logits(tf.clip_by_value(model.D_logits,1e-10,1.0),
                                        true_label * tf.ones_like(model.D)))

    model.d_loss_fake = tf.reduce_mean(
            sigmoid_cross_entropy_with_logits(tf.clip_by_value(model.D_logits_,1e-10,1.0),
                                              false_label * tf.ones_like(model.D_)))

    model.g_loss = tf.reduce_mean(
      sigmoid_cross_entropy_with_logits(tf.clip_by_value(model.D_logits_, 1e-10, 1.0),
                                        tf.ones_like(model.D_)))
    model.d_loss = model.d_loss_real + model.d_loss_fake

    model.d_sum = histogram_summary("d", model.D)
    model.d__sum = histogram_summary("d_", model.D_)
    model.G_sum = image_summary("G", model.G)
    model.G_sum = image_summary("inpt", model.inputs)

    model.g_loss_sum = scalar_summary("g_loss", model.g_loss)
    model.d_loss_sum = scalar_summary("d_loss", model.d_loss)
    model.d_loss_real_sum = scalar_summary("d_loss_real", model.d_loss_real)
    model.d_loss_fake_sum = scalar_summary("d_loss_fake", model.d_loss_fake)
    model.d_sum = merge_summary(
      [model.z_sum, model.d_sum, model.d_loss_real_sum, model.d_loss_sum])
    model.g_sum = merge_summary([model.z_sum, model.d__sum,
      model.G_sum, model.d_loss_fake_sum, model.g_loss_sum])

    model.g_opt = tf.train.AdamOptimizer(learning_rate=model.learning_rate, beta1=0.5)
    model.d_opt = tf.train.AdamOptimizer(learning_rate=model.learning_rate, beta1=0.5)
    t_vars = tf.trainable_variables()
    d_vars = [var for var in t_vars if 'd_' in var.name]
    g_vars = [var for var in t_vars if 'g_' in var.name]
    d_update = model.d_opt.minimize(model.d_loss, var_list=d_vars)
    g_update = model.g_opt.minimize(model.g_loss, var_list=g_vars)

    return d_update, g_update, [model.d_loss, model.g_loss], [model.d_sum, model.g_sum]

def WGAN_loss(model):
    model.g_opt = tf.train.AdamOptimizer(learning_rate=model.learning_rate, beta1=0.5)
    model.d_opt = tf.train.AdamOptimizer(learning_rate=model.learning_rate, beta1=0.5)

    model.G = model.generator(model, model.z, model.y)
    model.D_real = model.discriminator(model, model.inputs, model.y, reuse=False)
    model.D_fake = model.discriminator(model, model.G, model.y, reuse=True)
    model.g_loss = -tf.reduce_mean(model.D_fake)
    model.wp= -tf.reduce_mean(model.D_fake) + tf.reduce_mean(model.D_real)

    epsilon = tf.random_uniform(
        shape= [model.batch_size, 1,1,1],
        minval=0.,
        maxval=1.
    )
    x_hat = model.inputs + epsilon * (model.G - model.inputs)
    D_x_hat = model.discriminator(model, x_hat, model.y,reuse=True)
    grad_D_x_hat = tf.gradients(D_x_hat, [x_hat])[0]
    model.slopes = tf.sqrt(tf.reduce_sum(tf.square(grad_D_x_hat), reduction_indices=[1,2,3]))
    model.gradient_penalty = tf.reduce_mean((model.slopes - 1.) ** 2)
    model.d_loss = -model.wp + 10 * model.gradient_penalty

    t_vars = tf.trainable_variables()
    model.d_vars = [var for var in t_vars if 'd_' in var.name]
    model.g_vars = [var for var in t_vars if 'g_' in var.name]

    g_update = model.g_opt.minimize(model.g_loss, var_list=model.g_vars)
    d_update = model.d_opt.minimize(model.d_loss, var_list=model.d_vars)

    loss_ops = [model.d_loss, model.g_loss]

    model.G_sum = image_summary("G", model.G)
    model.g_loss_sum = scalar_summary("g_loss", model.g_loss)
    model.d_loss_sum = scalar_summary("d_loss", model.d_loss)
    model.wp_sum = scalar_summary("wasserstein_penalty", model.wp)
    model.gp_sum = scalar_summary("gradient_penalty", model.gradient_penalty)

    model.d_sum = merge_summary([model.d_loss_sum, model.wp_sum, model.gp_sum])
    model.g_sum = merge_summary([model.g_loss_sum, model.G_sum])
    return d_update, g_update, loss_ops, [model.d_sum, model.g_sum]

