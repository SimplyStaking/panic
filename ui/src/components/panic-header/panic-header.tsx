import { Component, getAssetPath, h } from '@stencil/core';
import { HOME_URL } from '../../utils/constants';

@Component({
  tag: 'panic-header',
  styleUrl: 'panic-header.scss',
  assetsDirs: ['../assets']
})
export class PanicHeader {

  render() {
    return (
      <svc-header imgPath={getAssetPath("../assets/logos/panic_logo.png")} imgPosition={"start"} imgLink={HOME_URL} />
    );
  }

}
