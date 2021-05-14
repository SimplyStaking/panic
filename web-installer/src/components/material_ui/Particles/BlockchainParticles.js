/* eslint-disable react/prefer-stateless-function */
import React, { Component } from 'react';
import Particles from 'react-particles-js';
import Chainlink from 'assets/icons/chainlink-link-logo.svg';
import Cosmos from 'assets/icons/cosmos-atom-logo.svg';
import Polkadot from 'assets/icons/polkadot-new-dot-logo.svg';
import Akash from 'assets/icons/akash-network-akt-logo.svg';
import Kusama from 'assets/icons/kusama-ksm-logo.svg';
import Ethereum from 'assets/icons/ethereum-eth-logo.svg';
import Binance from 'assets/icons/binance-coin-bnb-logo.svg';
import Secret from 'assets/icons/secret-scrt-logo.svg';

class CustomParticles extends Component {
  render() {
    return (
      <Particles
        height={window.outerHeight - 95}
        params={{
          particles: {
            collisions: {
              enable: true,
            },
            number: {
              value: 80,
              density: {
                enable: true,
                value_area: 1000,
              },
            },
            opacity: {
              random: {
                enable: true,
                minimumValue: 0.3,
              },
              value: {
                min: 100,
                max: 100,
              },
              animation: {
                count: 0,
                enable: false,
                speed: 0.5,
                sync: false,
                destroy: 'none',
                minimumValue: 0.3,
                startValue: 'random',
              },
            },
            line_linked: {
              blink: false,
              shadow: {
                enable: true,
                color: '#263089',
                blur: 1,
              },
              enable: true,
            },
            move: {
              speed: 0.2,
              out_mode: 'out',
            },
            shape: {
              type: ['image'],
              image: [
                {
                  src: Chainlink,
                  height: 20,
                  width: 17.272727273,
                },
                {
                  src: Cosmos,
                  height: 20,
                  width: 20,
                },
                {
                  src: Polkadot,
                  height: 20,
                  width: 14.950059928,
                },
                {
                  src: Akash,
                  height: 20,
                  width: 20,
                },
                {
                  src: Kusama,
                  height: 20,
                  width: 20,
                },
                {
                  src: Ethereum,
                  height: 20,
                  width: 12.278,
                },
                {
                  src: Binance,
                  height: 20,
                  width: 20,
                },
                {
                  src: Secret,
                  height: 20,
                  width: 20,
                },
              ],
            },
            color: {
              value: '#263089',
            },
            size: {
              value: 30,
              random: true,
              anim: {
                enable: false,
                speed: 0.1,
                size_min: 5,
                sync: true,
              },
            },
          },
          twinkle: {
            particles: {
              enable: true,
              frequency: 15,
              opacity: 1,
            },
          },
          retina_detect: false,
        }}
      />
    );
  }
}

export default CustomParticles;
