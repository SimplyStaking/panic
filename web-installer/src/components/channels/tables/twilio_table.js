import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  List,
  ListItem,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CancelIcon from '@material-ui/icons/Cancel';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

const TwilioTable = (props) => {
  const classes = useStyles();

  const {
    twilios,
    removeTwilioDetails,
  } = props;

  if (twilios.length === 0) {
    return <div />;
  }
  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell align="center">Account Sid</TableCell>
            <TableCell align="center">Authentication Token</TableCell>
            <TableCell align="center">Twilio Phone Number</TableCell>
            <TableCell align="center">Numbers to dial</TableCell>
            <TableCell align="center">Delete</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {twilios.map((twilio) => (
            <TableRow key={twilio.configName}>
              <TableCell component="th" scope="row">
                {twilio.configName}
              </TableCell>
              <TableCell align="center">{twilio.accountSid}</TableCell>
              <TableCell align="center">{twilio.authToken}</TableCell>
              <TableCell align="center">{twilio.twilioPhoneNo}</TableCell>
              <TableCell align="center">
                <div style={{ maxHeight: 70, overflow: 'auto' }}>
                  <List>
                    {twilio.twilioPhoneNumbersToDialValid.map((number) => (
                      <ListItem key={number}>
                        { number }
                      </ListItem>
                    ))}
                  </List>
                </div>
              </TableCell>
              <TableCell align="center">
                <Button onClick={() => { removeTwilioDetails(twilio); }}>
                  <CancelIcon />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

TwilioTable.propTypes = forbidExtraProps({
  twilios: PropTypes.arrayOf(PropTypes.shape({
    configName: PropTypes.string.isRequired,
    accountSid: PropTypes.string.isRequired,
    authToken: PropTypes.string.isRequired,
    twilioPhoneNo: PropTypes.string.isRequired,
    twilioPhoneNumbersToDialValid: PropTypes.arrayOf(
      PropTypes.string.isRequired,
    ).isRequired,
  })).isRequired,
  removeTwilioDetails: PropTypes.func.isRequired,
});

export default TwilioTable;
