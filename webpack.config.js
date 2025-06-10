const path = require("path");
const CopyPlugin = require("copy-webpack-plugin");
const HtmlPlugin = require("html-webpack-plugin");

function getHtmlPlugins(chunks) {
  return chunks.map(chunk => new HtmlPlugin({
    title: "Code n' Pipes",
    filename: `${chunk}.html`,
    chunks: [chunk],
  }));
}

module.exports = {
  mode: "development",
  devtool: 'cheap-module-source-map',
  entry: {
    popup: path.resolve('./src/popup/popup.tsx'),
    settings: path.resolve('./src/settings/settings.tsx'),
    background: path.resolve('./src/background/background.ts'),
    content: path.resolve('./src/content/content.ts')
    // Removed duplicate background entry
  },
  module: {
    rules: [
      {
        use: "ts-loader",
        test: /\.tsx?$/,
        exclude: /node_modules/,
      },
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader', 'postcss-loader'],
      },
    ],
  },
  plugins: [
    ...getHtmlPlugins(["popup", "settings"]),
    new CopyPlugin({
      patterns: [
        { from: path.resolve('src/assets/manifest.json'), to: path.resolve('dist') },
        { from: path.resolve('src/assets/icon.png'), to: path.resolve('dist') },
      ],
    }),
  ],
  resolve: {
    extensions: [".ts", ".tsx", ".js"],
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'dist'),
    clean: true, // Clean dist folder before each build
  },
  optimization: {
    splitChunks: {
      chunks(chunk) {
        // Don't split chunks for content and background scripts
        return chunk.name !== 'content' && chunk.name !== 'background';
      },
    },
  },
};