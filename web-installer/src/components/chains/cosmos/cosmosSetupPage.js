import React from 'react';
import { Grid, Box } from '@material-ui/core';
import Title from '../../global/title';
import MainText from '../../global/mainText';
import StepManager from '../../../containers/chains/cosmos/stepManager';
import Data from '../../../data/cosmos';

/*
 * Main cosmos setup page, this will be constant through out the cosmos chain
 * setup process. What will change is whatever the StepManager returns. This
 * depends on what is currently set in the state through redux. E.g if the step
 * is set as the NODES_STEP in redux then the nodes form and table will be
 * rendered.
*/
function CosmosSetupPage() {
  return (
    <div>
      <Title
        text={Data.cosmos.title}
      />
      <MainText
        text={Data.cosmos.description}
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
              <StepManager />
            </Grid>
          </Grid>
        </Box>
      </Box>
    </div>
  );
}

export default CosmosSetupPage;
