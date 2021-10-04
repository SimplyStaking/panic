import { Env } from '@stencil/core';

export enum Severity {
    CRITICAL = 'Critical',
    WARNING = 'Warning',
    ERROR = 'Error'
}

export const HOME_URL = '/';
export const baseChainsNames: string[] = ["cosmos", "general", "chainlink", "substrate"];
export const apiURL: string = `https://${Env.API_IP}:${Env.API_PORT}/server/`;
export const criticalIcon = { 'svc-button': { props: { 'icon-name': 'skull', 'icon-position': 'icon-only', 'color': 'dark' } } };
export const warningIcon = { 'svc-button': { props: { 'icon-name': 'warning', 'icon-position': 'icon-only', 'color': 'warning' } } };
export const errorIcon = { 'svc-button': { props: { 'icon-name': 'alert-circle', 'icon-position': 'icon-only', 'color': 'danger' } } };

// Test Related
export const fetchMock: any = fetch as any;