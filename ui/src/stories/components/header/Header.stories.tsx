import React from 'react';
// also exported from '@storybook/react' if you can deal with breaking changes in 6.1
import { Story, Meta } from '@storybook/react/types-6-0';
// import { Button } from '@material-ui/core';

import { Header, HeaderProps } from './Header';
import { Button } from '../button/Button';

export default {
  title: 'Header',
  component: Header,
} as Meta;


const changePageAlert = (event: React.ChangeEvent<{ value: unknown }>) => {
  alert(`You have changed to network ${event.target.value as string}!`);
}

const Template: Story<HeaderProps> = (args) => <Header {...args} />;

export const Default = Template.bind({});
Default.args = {
  networkPage: 'dashboard',
  toNetworkPage: changePageAlert,
};


export const Cosmos = Template.bind({});
Cosmos.args = {
  ...Default.args,
  networkPage: 'cosmos'
}

export const Susbtrate = Template.bind({});
Susbtrate.args = {
  ...Default.args,
  networkPage: 'substrate'
}

export const Chainlink = Template.bind({});
Chainlink.args = {
  ...Default.args,
  networkPage: 'chainlink'
}