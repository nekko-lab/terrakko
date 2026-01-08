import { TerrakkoBot } from './bot/TerrakkoBot';
import { DatabaseManager } from './infrastructure/db/Database';
import { Config } from './infrastructure/config/Config';
import { Logger } from './utils/Logger';

let bot: TerrakkoBot | null = null;

/**
 * グレースフルシャットダウン
 */
async function shutdown(): Promise<void> {
  Logger.info('Shutting down...');

  if (bot) {
    await bot.destroy();
  }

  // データベースをクローズ
  DatabaseManager.getInstance().close();

  process.exit(0);
}

/**
 * メイン関数
 */
async function main(): Promise<void> {
  try {
    // 設定を検証
    Config.validate();

    // データベースを初期化
    DatabaseManager.getInstance().initialize();

    // Botを作成してログイン
    bot = new TerrakkoBot();
    await bot.login();

    // シグナルハンドラを設定
    process.on('SIGINT', () => shutdown());
    process.on('SIGTERM', () => shutdown());

    // 未処理のエラーをキャッチ
    process.on('unhandledRejection', (reason) => {
      Logger.error('Unhandled Rejection', reason as Error);
    });

    process.on('uncaughtException', (error) => {
      Logger.error('Uncaught Exception', error);
      shutdown();
    });

    Logger.info('Bot started successfully');
  } catch (error) {
    Logger.error('Failed to start bot', error as Error);
    process.exit(1);
  }
}

// メイン関数を実行
main().catch((error) => {
  Logger.error('Fatal error', error);
  process.exit(1);
});
