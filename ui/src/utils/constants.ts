import { Env } from '@stencil/core';

export const HOME_URL = '/';
export const baseChainsNames: string[] = ["cosmos", "general", "chainlink", "substrate"];
export const apiURL: string = `https://${Env.API_IP}:${Env.API_PORT}/server/`;

// Test Related
export const fetchMock: any = fetch as any;