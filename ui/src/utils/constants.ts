import { Env } from '@stencil/core';
import { Chain } from '../interfaces/chains';

export const HOME_URL = '/';
export const baseChainsNames: string[] = ["cosmos", "general", "chainlink", "substrate"];
export const apiURL: string = `https://${Env.API_IP}:${Env.API_PORT}/server/`;
export const allChain: Chain = {
    name: 'all', id: 'all', repos: [], systems: [],
    criticalAlerts: 0, warningAlerts: 0, errorAlerts: 0,
    totalAlerts: 0, active: true
};

// Test Related
export const fetchMock: any = fetch as any;