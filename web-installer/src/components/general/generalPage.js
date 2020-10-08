import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import { Box } from '@material-ui/core';
import Title from '../global/title';
import MainText from '../global/mainText';
import NavigationButtonContainer from
  '../../containers/global/navigationButtonContainer';
import GeneralAccordion from './generalAccordion';
import SystemIcon from '../../assets/icons/system.svg';
import TimeIcon from '../../assets/icons/time.svg';
import {
  CONFIGURE, GENERAL_SETUP_PAGE, GENERAL, PERIODIC, NEXT, USERS_PAGE,
  CHAINS_PAGE, BACK,
} from '../../constants/constants';
import PeriodicFormContainer from '../../containers/general/periodicContainer';
import Data from '../../data/general';

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  },
  paper: {
    padding: theme.spacing(2),
    textAlign: 'center',
    color: theme.palette.text.primary,
  },
  icon: {
    paddingRight: '1rem',
  },
  heading: {
    fontSize: theme.typography.pxToRem(15),
    fontWeight: theme.typography.fontWeightRegular,
  },
}));

function GeneralsPage() {
  const classes = useStyles();

  return (
    <div>
      <Title
        text={Data.general.title}
      />
      <MainText
        text={Data.general.description}
      />
      <Box p={2} className={classes.root}>
        <Box
          p={3}
          border={1}
          borderRadius="borderRadius"
          borderColor="grey.300"
        >
          <GeneralAccordion
            icon={TimeIcon}
            name={PERIODIC}
            button={( <div />)}
            form={(<PeriodicFormContainer />)}
          />
          <GeneralAccordion
            icon={SystemIcon}
            name={GENERAL}
            button={(
              <NavigationButtonContainer
                text={CONFIGURE}
                navigation={GENERAL_SETUP_PAGE}
              />
            )}
            form={(<div />)}
          />
        </Box>
      </Box>
      <NavigationButtonContainer
        text={NEXT}
        navigation={USERS_PAGE}
      />
      <NavigationButtonContainer
        text={BACK}
        navigation={CHAINS_PAGE}
      />
    </div>
  );
}

export default GeneralsPage;
