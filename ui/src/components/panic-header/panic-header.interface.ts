import {BaseChain} from "../../interfaces/chains";
import {DropdownMenuOptionType} from "@simply-vc/uikit/dist/types/types/dropdownmenu";

export interface PanicHeaderInterface {

    /**
     * Array of base chains used to build the array of links assigned to
     * {@link PanicHeaderInterface._menuOptions _menuOptions} prop.
     */
    _baseChains: BaseChain[],

    /**
     * Array of links displayed in the dropdown menu.
     */
    _menuOptions: DropdownMenuOptionType[],

    /**
     * Whether the menu should be displayed or not. Default is `true`.
     */
    showMenu: boolean
}
