import React from 'react';
import { Box } from '@material-ui/core';
import HelpIcon from '@material-ui/icons/Help';
import SettingsIcon from '@material-ui/icons/Settings';
import ComputerIcon from '@material-ui/icons/Computer';
import GridContainer from 'components/material_ui/Grid/GridContainer';
import GridItem from 'components/material_ui/Grid/GridItem';
import InfoArea from 'components/material_ui/InfoArea/InfoArea';
import Data from 'data/chains';
import useStyles from 'assets/jss/material-kit-react/views/landingPageSections/productStyle';

export default function DescriptionSection() {
  const classes = useStyles();
  return (
    <div className={classes.section}>
      <Box pb={5}>
        <GridContainer justify="center">
          <GridItem xs={12} sm={12} md={8}>
            <h1 className={classes.title}>{Data.chains.subtitle_1}</h1>
          </GridItem>
        </GridContainer>
      </Box>
      <div>
        <GridContainer>
          <GridItem xs={12} sm={12} md={4}>
            <InfoArea
              title={Data.chains.what_title}
              description={(
                <div>
                  <ul>
                    <li>{Data.chains.what_1}</li>
                    <li>{Data.chains.what_2}</li>
                  </ul>
                </div>
              )}
              icon={HelpIcon}
              iconColor="#000000"
              vertical
            />
          </GridItem>
          <GridItem xs={12} sm={12} md={4}>
            <InfoArea
              title={Data.chains.supported_title}
              description={(
                <div>
                  <ul>
                    <li>{Data.chains.chain_1}</li>
                    <li>{Data.chains.chain_2}</li>
                    <li>{Data.chains.chain_3}</li>
                  </ul>
                </div>
              )}
              icon={ComputerIcon}
              iconColor="#000000"
              vertical
            />
          </GridItem>
          <GridItem xs={12} sm={12} md={4}>
            <InfoArea
              title={Data.chains.how_title}
              description={(
                <div>
                  <ul>
                    <li>{Data.chains.how_1}</li>
                    <li>{Data.chains.how_2}</li>
                    <li>{Data.chains.how_3}</li>
                  </ul>
                </div>
              )}
              icon={SettingsIcon}
              iconColor="#000000"
              vertical
            />
          </GridItem>
        </GridContainer>
        <GridContainer>
          <GridItem xs={12} sm={12} md={12}>
            <h1 className={classes.title}>{Data.chains.subtitle_2}</h1>
          </GridItem>
        </GridContainer>
      </div>
    </div>
  );
}
