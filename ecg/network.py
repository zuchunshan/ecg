
def add_conv_layers(acts, **params):
    from keras.layers.convolutional import Convolution1D
    from keras.layers import Dropout, Activation, BatchNormalization
    from keras.layers.noise import GaussianNoise
    subsample_lengths = params["conv_subsample_lengths"]
    for subsample_length in subsample_lengths:
        if params.get("gaussian_noise", 0) > 0:
            acts = GaussianNoise(params["gaussian_noise"])(acts)
        acts = Convolution1D(
            nb_filter=params["conv_num_filters"],
            filter_length=params["conv_filter_length"],
            border_mode='same',
            subsample_length=subsample_length,
            init=params["conv_init"])(acts)
        if params.get("use_batch_norm", False) is True:
            acts = BatchNormalization()(acts)

        activation_fn = params["conv_activation"]
        if activation_fn == 'prelu':
            from keras.layers.advanced_activations import PReLU
            acts = PReLU()(acts)
        elif activation_fn == 'elu':
            from keras.layers.advanced_activations import ELU
            acts = ELU()(acts)
        elif activation_fn == 'leaky_relu':
            from keras.layers.advanced_activations import LeakyReLU
            acts = LeakyReLU()(acts)
        else:
            acts = Activation(activation_fn)(acts)

        if params.get("conv_dropout", 0) > 0:
            acts = Dropout(params["conv_dropout"])(acts)
    return acts


def add_recurrent_layers(acts, **params):
    from keras.layers.recurrent import LSTM, GRU
    from keras.layers.wrappers import Bidirectional
    for i in range(params.get("recurrent_layers", 0)):
        rt = params["recurrent_type"]
        if rt == 'GRU':
            Recurrent = GRU
        elif rt == 'LSTM':
            Recurrent = LSTM
        rec_layer = Recurrent(
                    params["recurrent_hidden"],
                    dropout_W=params["recurrent_dropout"],
                    dropout_U=params["recurrent_dropout"],
                    return_sequences=True)
        if params["recurrent_is_bidirectional"] is True:
            acts = Bidirectional(rec_layer)(acts)
        else:
            acts = rec_layer(acts)
    return acts


def add_dense_layers(acts, **params):
    from keras.layers.core import Dense
    from keras.layers.wrappers import TimeDistributed
    from keras.layers import Dropout
    from keras.regularizers import l2
    for i in range(params.get("dense_layers", 0)):
        acts = TimeDistributed(Dense(
            params["dense_hidden"],
            activation=params["dense_activation"],
            init=params["dense_init"],
            W_regularizer=l2(params["dense_l2_penalty"])))(acts)
        if params.get("dense_dropout", 0) > 0:
            acts = Dropout(params["dense_dropout"])(acts)
    return acts


def add_output_layer(acts, **params):
    from keras.layers.core import Dense, Activation
    from keras.layers.wrappers import TimeDistributed
    acts = TimeDistributed(Dense(params["num_categories"]))(acts)
    return Activation('softmax')(acts)


def add_compile(model, **params):
    from keras.optimizers import Adam
    optimizer = Adam(lr=params["learning_rate"], clipnorm=params["clipnorm"])

    model.compile(loss='categorical_crossentropy',
                  optimizer=optimizer,
                  metrics=['accuracy'])


def build_network(**params):
    from keras.models import Model
    from keras.layers import Input
    inputs = Input(shape=params['input_shape'],
                   dtype='float32',
                   name='inputs')
    acts = add_conv_layers(inputs, **params)
    acts = add_recurrent_layers(acts, **params)
    acts = add_dense_layers(acts, **params)
    output = add_output_layer(acts, **params)
    model = Model(input=[inputs], output=[output])
    add_compile(model, **params)
    return model
