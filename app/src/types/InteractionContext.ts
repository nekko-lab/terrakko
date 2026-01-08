import { Interaction } from 'discord.js';

export interface InteractionContext {
  interaction: Interaction;
  userId: string;
  userName: string;
}
