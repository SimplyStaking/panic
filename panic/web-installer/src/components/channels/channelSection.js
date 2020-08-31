import React from 'react'
import PropTypes from 'prop-types';
import ChannelAccordionContainer from '../../containers/';

function ChannelSection(props) {
  const { tableContainer } = props;

  return (
    <div>
        <ChannelAccordionContainer />
        {tableContainer}
    </div>
  )
}

ChannelSection.propTypes = {
  tableContainer: PropTypes.element.isRequired,
};

export default ChannelSection;