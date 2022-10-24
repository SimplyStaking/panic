export type TypeMessage = 'error' | 'warning' | 'info';

export interface IMessage {
    type: TypeMessage,
    description: string,
    name: string
}