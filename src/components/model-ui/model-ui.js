import React, { useState } from 'react';
import LottiePlayer from 'react-lottie';
import { connect } from 'react-redux';
import {
  toggleKedroRun,
  updateFeatureChanges,
  updateTargetChanges,
  updateModelEvaluatorChanges,
  updateModelObjectChanges,
} from '../../actions/kedro-run';
import IconButton from '../ui/icon-button';
import CloseIcon from '../icons/close';
import { MultipleSelectCheckmarks } from '../ui/checkmarks/checkmarks';
import ReactCodeSinppet from 'react-code-snippet';
import animationData from '../lotties/loading.json';

import features from './mock-data/features';
import targets from './mock-data/targets';
import modelClassObjects from './mock-data/model-class-objects';
import modelEvaluators from './mock-data/model_evaluators';

import './model-ui.css';

const options = {
  loop: true,
  autoplay: true,
  animationData: animationData,
  rendererSettings: {
    preserveAspectRatio: 'xMidYMid slice',
  },
};

const Loading = () => {
  return (
    <div className="loading-wrapper">
      <LottiePlayer
        height={250}
        width={250}
        isClickToPauseDisabled
        options={options}
      />
    </div>
  );
};

const renderSnippet = (featureList, target, modelObject, modelEvaluator) => {
  const feature =
    featureList.length > 0
      ? featureList.map(
          (each) => `
  - ${each}`
        )
      : `
  -`;
  return (
    <ReactCodeSinppet
      code={`features:${feature}

target:
  - ${target}

model_class:
  object: ${modelObject}
  instantiate: False
  
model_evaluators:
  ${
    modelEvaluator[0] === 'sklearn.metrics.r2_score'
      ? `r2_score:`
      : `mean_squared_error:`
  }
    object: ${modelEvaluator}`}
    />
  );
};

const ModelUI = ({
  dismissed,
  setDismiss,
  onTriggerKedroRun,
  runConfig,
  runLoading,
  onUpdateFeatureChanges,
  onUpdateTargetChanges,
  onUpdateModelEvaluatorChanges,
  onUpdateModelObjectChanges,
}) => {
  const [expand, setExpand] = useState(false);
  const [loading, setLoading] = useState(false);
  // multiple choices
  const [feature, setFeature] = useState([]);
  const [target, setTarget] = useState([]);

  console.log('runLoading', runLoading);

  // single choice
  const [modelObject, setModelObject] = useState([]);
  // const [instantiate, setInstantiate] = useState([]);
  const [modelEvaluator, setModelEvaluator] = useState([]);

  const handleFeaturesChange = (event) => {
    const {
      target: { value },
    } = event;
    console.log('value', value);
    setFeature(
      // On autofill we get a stringified value.
      typeof value === 'string' ? value.split(',') : value
    );
    onUpdateFeatureChanges(value);
  };

  const handleTargetChange = (event) => {
    const {
      target: { value },
    } = event;
    setTarget(
      // On autofill we get a stringified value.
      typeof value === 'string' ? value.split(',') : value
    );
    onUpdateTargetChanges(value);
  };

  const handleModelObjectChange = (event) => {
    const {
      target: { value },
    } = event;
    setModelObject(
      // On autofill we get a stringified value.
      typeof value === 'string' ? value.split(',') : value
    );
    onUpdateModelObjectChanges(value);
  };

  const handleModelEvaluatorChange = (event) => {
    const {
      target: { value },
    } = event;
    setModelEvaluator(
      // On autofill we get a stringified value.
      typeof value === 'string' ? value.split(',') : value
    );
    onUpdateModelEvaluatorChanges(value);
  };

  const onClickKedroRun = () => {
    setLoading(true);
    onTriggerKedroRun();

    setTimeout(() => setLoading(false), 30000);
  };
  if (expand) {
    return (
      <>
        <div className="model-ui-expanded-header">
          <p>Model UI</p>

          <div className="close-button-container">
            <IconButton
              container={React.Fragment}
              ariaLabel="Close Model UI Panel"
              className="close-button"
              icon={CloseIcon}
              onClick={() => setExpand(false)}
            />
          </div>
        </div>
        <div className="model-ui-expanded-detail">
          <div className="model-ui-checkmarks-wrapper">
            <div className="model-ui-select-title">1. Feature:</div>
            <MultipleSelectCheckmarks
              values={features}
              selectedValue={feature}
              onSelect={handleFeaturesChange}
              width={300}
              multiple
            />

            <div className="model-ui-select-title">2. Target:</div>
            <MultipleSelectCheckmarks
              values={targets}
              selectedValue={target}
              onSelect={handleTargetChange}
              width={300}
              multiple
            />

            <div className="model-ui-select-title">3. Model class object:</div>
            {/* <div className="model-ui-select-title">Object:</div> */}
            <MultipleSelectCheckmarks
              values={modelClassObjects}
              selectedValue={modelObject}
              onSelect={handleModelObjectChange}
              width={400}
              multiple={false}
            />
            {/* <div className="model-ui-select-title">Instantiate:</div>
            <MultipleSelectCheckmarks
              values={['true', 'false']}
              selectedValue={instantiate}
              onSelect={handleInstantiateChange}
              width={100}
              multiple={false}
            /> */}

            <div className="model-ui-select-title">4. Model Evaluators:</div>
            <MultipleSelectCheckmarks
              values={modelEvaluators}
              selectedValue={modelEvaluator}
              onSelect={handleModelEvaluatorChange}
              width={400}
              multiple={false}
            />

            <div className="model-ui-select-title">
              {renderSnippet(feature, target, modelObject, modelEvaluator)}
            </div>
          </div>

          <button className="model-ui-button--run" onClick={onClickKedroRun}>
            Kedro Run
          </button>
          {runLoading && <Loading />}
        </div>
      </>
    );
  }

  return (
    <div className="update-reminder-unexpanded">
      <p>Model UI</p>
      <div className="buttons-container">
        <button className="kedro" onClick={() => setExpand(true)}>
          Expand
        </button>
        <button className="kedro" onClick={() => setDismiss(true)}>
          Dismiss
        </button>
      </div>
    </div>
  );
};

export const mapStateToProps = (state) => ({
  runConfig: state.runConfig,
  runLoading: state.loading.run,
});

export const mapDispatchToProps = (dispatch) => ({
  onTriggerKedroRun: (event) => {
    dispatch(toggleKedroRun());
  },
  onUpdateFeatureChanges: (value) => {
    dispatch(updateFeatureChanges(value));
  },
  onUpdateTargetChanges: (value) => {
    dispatch(updateTargetChanges(value));
  },
  onUpdateModelEvaluatorChanges: (value) => {
    dispatch(updateModelEvaluatorChanges(value));
  },
  onUpdateModelObjectChanges: (value) => {
    dispatch(updateModelObjectChanges(value));
  },
});

export default connect(mapStateToProps, mapDispatchToProps)(ModelUI);
