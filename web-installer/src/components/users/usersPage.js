import React from 'react';
import { Grid, Box } from '@material-ui/core';
import Title from '../global/title';
import MainText from '../global/mainText';
import NavigationButtonContainer from
  '../../containers/global/navigationButtonContainer';
import { UsersFormContainer, UsersTableContainer } from
  '../../containers/users/usersContainer';
import { GENERAL_PAGE, BACK } from '../../constants/constants';
import SaveConfig from '../../containers/global/saveConfig';
import Data from '../../data/users';

function UsersPage() {
  return (
    <div>
      <Title
        text={Data.users.title}
      />
      <MainText
        text={Data.users.description}
      />
      <Box p={2} className="flex_root">
        <Box
          p={3}
          border={1}
          borderRadius="borderRadius"
          borderColor="grey.300"
        >
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <UsersFormContainer />
              <UsersTableContainer />
            </Grid>
          </Grid>
        </Box>
      </Box>
      <Grid container spacing={3} justify="center" alignItems="center">
        <Grid item xs={2}>
          <Box px={2}>
            <NavigationButtonContainer
              text={BACK}
              navigation={GENERAL_PAGE}
            />
          </Box>
        </Grid>
        <Grid item xs={8} />
        <Grid item xs={2}>
          <Box px={2}>
            <SaveConfig />
          </Box>
        </Grid>
      </Grid>
    </div>
  );
}

export default UsersPage;
