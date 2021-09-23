import { Env, h } from '@stencil/core';
import { Chain } from '../interfaces/chains';

export const HOME_URL = '/';
export const baseChainsNames: string[] = ["cosmos", "general", "chainlink", "substrate"];
export const apiURL: string = `https://${Env.API_IP}:${Env.API_PORT}/server/`;
export const allChain: Chain = {
    name: 'all', id: 'all', repos: [], systems: [],
    criticalAlerts: 0, warningAlerts: 0, errorAlerts: 0,
    alerts: [], active: true
};

export const criticalIcon = <svc-button icon-name="skull" icon-position="icon-only"></svc-button>;
export const warningIcon = <svc-button icon-name="warning" icon-position="icon-only"></svc-button>;
export const errorIcon = <svc-button icon-name="alert-circle" icon-position="icon-only"></svc-button>;

// Test Related
export const fetchMock: any = fetch as any;