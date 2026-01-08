import {
  EmbedBuilder,
  ActionRowBuilder,
  ButtonBuilder,
  StringSelectMenuBuilder
} from 'discord.js';
import { EmbedBuilder as CustomEmbedBuilder } from './EmbedBuilder';
import { ComponentFactory } from './ComponentFactory';
import { VM } from '../domain/vm/VM';

export class MenuBuilder {
  /**
   * メインメニューを構築
   */
  public static buildMainMenu(userName: string): {
    embeds: EmbedBuilder[];
    components: ActionRowBuilder<ButtonBuilder | StringSelectMenuBuilder>[];
  } {
    return {
      embeds: [CustomEmbedBuilder.createMainMenuEmbed(userName)],
      components: [ComponentFactory.createMainMenuButtons()]
    };
  }

  /**
   * VM情報メニューを構築
   */
  public static buildVMInfoMenu(vm: VM): {
    embeds: EmbedBuilder[];
    components: ActionRowBuilder<ButtonBuilder>[];
  } {
    return {
      embeds: [CustomEmbedBuilder.createVMInfoEmbed(vm)],
      components: ComponentFactory.createPowerControlButtons(vm)
    };
  }
}
