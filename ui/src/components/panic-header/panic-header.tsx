import {Component, getAssetPath, h, Prop} from '@stencil/core';
import {BaseChain} from '../../interfaces/chains';
import {HOME_URL} from '../../utils/constants';
import {ChainsAPI} from '../../utils/chains';
import {DropdownMenuOptionType} from '@simply-vc/uikit/dist/types/types/dropdownmenu';
import {PanicHeaderInterface} from './panic-header.interface';

@Component({
    tag: 'panic-header',
    styleUrl: 'panic-header.scss',
    assetsDirs: ['../assets']
})
export class PanicHeader implements PanicHeaderInterface {

    _baseChains: BaseChain[] = [];
    _menuOptions: DropdownMenuOptionType[] = [];
    @Prop() showMenu: boolean = true;

    async componentWillLoad() {
        this._baseChains = await ChainsAPI.getAllBaseChains();

        for (let i = 0; i < this._baseChains.length; i++) {
            const baseChain = this._baseChains[i];
            this._menuOptions.push({
                label: baseChain.name,
                url: `/systems-overview/${baseChain.name}`
            });
        }
    }

    render() {
        return (
            <svc-header
                imgPath={getAssetPath("../assets/logos/panic_logo.png")}
                imgPosition={"start"} imgURL={HOME_URL}
                menuPosition={"end"}
            >
                {
                    this.showMenu &&
                    <div slot={"menu"} class={"panic-header__menu"}>
                        {
                            this._menuOptions.length > 0 &&
                                <svc-dropdown-menu
                                  label={"Networks"}
                                  options={this._menuOptions}
                                />
                        }
                        <svc-dropdown-menu label={"Settings"} options={[
                            {label: "Chains", url: "/settings/chains"},
                            {label: "Channels", url: "/settings/channels"}
                        ]}/>
                    </div>
                }
            </svc-header>
        );
    }
}
