import {Component, getAssetPath, h, Host} from '@stencil/core';
import {PanicFooterInterface} from './panic-footer.interface';

@Component({
    tag: 'panic-footer',
    styleUrl: 'panic-footer.scss',
    assetsDirs: ['assets']
})
export class PanicFooter implements PanicFooterInterface {

    _twitterURL: string = 'https://twitter.com/Simply_VC';
    _githubURL: string = 'https://github.com/SimplyVC';
    _mediumURL: string = 'https://medium.com/simply-vc';
    _telegramURL: string = 'https://t.me/SimplyVC';
    _websiteURL: string = 'https://simply-vc.com.mt';
    _telegramLogoSVG: string = 'telegram_logo.svg';
    _simplyVcLogoSVG: string = 'simplyvc_logo.svg';

    render() {
        return (
            <Host>
                <svc-footer color="primary" headline-position="start"
                            headline="Developed by SimplyVC">
                    <svc-buttons-container position="end">
                        <svc-button
                            icon-name="logo-twitter"
                            href={this._twitterURL}
                            target="_blank"
                        />
                        <svc-button
                            icon-name="logo-github"
                            href={this._githubURL}
                            target="_blank"
                        />
                        <svc-button
                            icon-name="logo-medium"
                            href={this._mediumURL}
                            target="_blank"
                        />
                        <svc-button
                            icon-src={getAssetPath(`./assets/${this._telegramLogoSVG}`)}
                            href={this._telegramURL}
                            target="_blank"
                        />
                        <svc-button
                            icon-src={getAssetPath(`./assets/${this._simplyVcLogoSVG}`)}
                            href={this._websiteURL}
                            target="_blank"
                        />
                    </svc-buttons-container>
                </svc-footer>
            </Host>
        );
    }
}
