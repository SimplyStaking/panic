import React from 'react';
import { AppBar, Toolbar, Button, IconButton } from '@material-ui/core';
import MenuIcon from '@material-ui/icons/Menu';
import { MenuItem, FormControl, Select} from '@material-ui/core';
// import { Button } from '../button/Button';
// import './header.css';

export interface HeaderProps {

  /** 
   * List of possible network pages that you can chose from.
  */
  networkPage?: 'cosmos' | 'substrate' | 'chainlink' | 'dashboard';

  /**
   * Function to handle the change page to a specific Network page.
   */
  toNetworkPage?: (event: any) => void;
}

// TODO: Change to our own Typography
// TODO: Change to our own Button
// TODO: FormControl to our own
export const Header: React.FC<HeaderProps> = ({
  networkPage = 'dashboard',
  toNetworkPage
  }: HeaderProps) => (
  <AppBar position="static">
    <Toolbar>
      <IconButton edge="start" color="inherit" aria-label="menu">
        <MenuIcon />
      </IconButton>
      <FormControl variant="filled">
        <Select
          labelId="demo-simple-select-filled-label"
          id="demo-simple-select-filled"
          displayEmpty
          value={networkPage}
          onChange={toNetworkPage}
        >
          <MenuItem value={'dashboard'}>Networks</MenuItem>
          <MenuItem value={'cosmos'}>Cosmos</MenuItem>
          <MenuItem value={'substrate'}>Substrate</MenuItem>
          <MenuItem value={'chainlink'}>Chainlink</MenuItem>
        </Select>
      </FormControl>
      <Button color="inherit">Logout</Button>
    </Toolbar>
  </AppBar>
);
