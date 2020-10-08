import React from 'react';
import { Grid, Box } from '@material-ui/core';
import Title from '../../global/title';
import MainText from '../../global/mainText';
import StepManager from '../../../containers/chains/substrate/stepManager';
import Data from '../../../data/substrate';

function SubstrateSetupPage() {
  return (
    <div>
      <Title
        text={Data.substrate.title}
      />
      <MainText
        text={Data.substrate.description}
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

export default SubstrateSetupPage;
