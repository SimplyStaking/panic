import { Component, Host, h, State } from '@stencil/core';
import { BaseChains, Chain } from '../../interfaces/chains';
import { baseChainsNames } from '../../utils/constants';
import { capitalizeFirstLetter } from '../../utils/helpers';

@Component({
  tag: 'panic-dashboard-overview',
  styleUrl: 'panic-dashboard-overview.css'
})
export class PanicDashboardOverview {
  // Hard-coded for now. To use ENV variables in the future.
  private apiURL: string = `https://${"localhost"}:${"9000"}/server/`;
  private baseChains: BaseChains[] = [];
  private updater: number;
  private updateFrequency: number = 3000;
  @State() alertsChanged: Boolean = false;

  async componentWillLoad() {
    try {
      const monitorablesInfo: Response = await fetch(this.apiURL + 'redis/monitorablesInfo',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            "baseChains": baseChainsNames
          })
        }
      );

      const data: any = await monitorablesInfo.json();

      for (const baseChain in data.result) {
        if (data.result[baseChain]) {
          var currentChains: Chain[] = [];
          var index: number = 0;
          for (const currentChain in data.result[baseChain]) {
            // Systems case.
            var currentSystems: string[] = [];
            for (const system of data.result[baseChain][currentChain].monitored.systems) {
              currentSystems.push(Object.keys(system)[0]);
            }

            // Repos case.
            var currentRepos: string[] = [];
            for (const type of Object.keys(data.result[baseChain][currentChain].monitored)) {
              if (type.includes('repo')) {
                for (const repo of data.result[baseChain][currentChain].monitored[type]) {
                  currentRepos.push(Object.keys(repo)[0]);
                }
              }
            }

            currentChains.push({
              name: capitalizeFirstLetter(currentChain),
              id: data.result[baseChain][currentChain].parent_id,
              repos: currentRepos,
              systems: currentSystems,
              criticalAlerts: 0,
              warningAlerts: 0,
              errorAlerts: 0,
              totalAlerts: 0,
              active: index == 0
            });

            index++;
          }

          this.baseChains.push({
            name: capitalizeFirstLetter(baseChain),
            chains: currentChains
          });
        }
      }

      await this.updateAllAlertsOverview(true);

      this.updater = window.setInterval(async () => {
        await this.updateAllAlertsOverview(false);
      }, this.updateFrequency);
    } catch (error: any) {
      console.error(error);
    }
  }

  async updateAllAlertsOverview(initialCall: Boolean): Promise<void> {
    var changed: Boolean = false;
    var result: {} = {};
    for (var baseChain of this.baseChains) {
      for (var chain of baseChain.chains) {
        if (chain.active) {
          result = await this.getAlertsOverview(chain, initialCall);
          chain = result['chain'];

          if (!initialCall && !changed && result['changed']) {
            changed = true;
          }
        }
      }
    }

    if (changed) {
      this.alertsChanged = !this.alertsChanged;
    }
  }

  async getAlertsOverview(chain: Chain, initialCall: Boolean): Promise<{ chain: Chain, changed: Boolean }> {
    var changed: Boolean = false;
    var chainSources = { parentIds: {} };
    chainSources.parentIds[chain.id] = { systems: [], repos: [] };
    chainSources.parentIds[chain.id].systems = chain.systems;
    chainSources.parentIds[chain.id].repos = chain.repos;

    try {
      const alertsOverview = await fetch(this.apiURL + 'redis/alertsOverview',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(chainSources)
        });

      const data: any = await alertsOverview.json();

      if (!initialCall && ((data.result[chain.id].critical != chain.criticalAlerts) ||
        (data.result[chain.id].warning != chain.warningAlerts) ||
        (data.result[chain.id].error != chain.errorAlerts))) {
        changed = true;
      }

      chain.criticalAlerts = data.result[chain.id].critical;
      chain.warningAlerts = data.result[chain.id].warning;
      chain.errorAlerts = data.result[chain.id].error;
      chain.totalAlerts = chain.criticalAlerts + chain.warningAlerts + chain.errorAlerts;

    } catch (error: any) {
      console.error(error);
    }

    return { chain: chain, changed: changed };
  }

  disconnectedCallback() {
    window.clearInterval(this.updater);
  }

  render() {
    const alertsColors: string[] = ['#f4dd77', '#f7797b', '#a39293'];
    const noAlertsColors: string[] = ['#b0ea8f'];
    const cols = [{ title: 'Alert', type: 'string' }, { title: 'Amount', type: 'number' }];

    return (
      <Host>
        <panic-header></panic-header>
        {this.baseChains.length > 0 && <svc-content-container>
          {this.baseChains.map((baseChain) =>
            <svc-surface label={baseChain.name}>
              {baseChain.chains.map((chain) => {
                return chain.active && <svc-card class="chain-card">
                  {/* A normal pie chart with the data is shown if there are any alerts. Otherwise,
                      A green pie chart is shown with no text and without a tooltip */}
                  {chain.totalAlerts > 0 ?
                    <svc-pie-chart key="alerts" slot="small" colors={alertsColors} cols={cols}
                      rows={[['Warning', chain.warningAlerts], ['Critical', chain.criticalAlerts], ['Error', chain.errorAlerts]]}>
                    </svc-pie-chart> :
                    <svc-pie-chart key="no alerts" slot="small" colors={noAlertsColors} cols={cols} rows={[['', 1]]}
                      pie-slice-text="none"
                      tooltip-trigger="none">
                    </svc-pie-chart>}
                </svc-card>
              })}
              <svc-label color="dark" position="start">This section displays only warning, critical and error alerts. For a full report, check <b><u>Alerts Overview.</u></b></svc-label>
            </svc-surface>
          )}
        </svc-content-container>}
        <panic-footer></panic-footer>
      </Host >
    );
  }
}
