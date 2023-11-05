module.exports = {
  mode: 'production',
  entry: {
    'index': './index.ts',
    'edit_mcdict': './edit_mcdict.ts',
  },
  output: {
    filename: '[name].js',
  },
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: 'ts-loader',
      },
    ],
  },
  resolve: {
    extensions: [
      '.ts', '.js',
    ],
  },
};
