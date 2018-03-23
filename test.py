from glob import glob
from string import ascii_lowercase
from collections import defaultdict
import pickle
import numpy as np
from prefix_beam_search import prefix_beam_search, prefix_beam_search_log_space
import time


class LanguageModel(object):
  """
  Loads a dictionary mapping between prefixes and probabilities.
  """

  def __init__(self, lm_file):
    """
    Initializes the language model.

    Args:
      lm_file (str): Path to dictionary mapping between prefixes and lm probabilities.
    """
    lm = pickle.load(open(lm_file, 'rb'))
    self._model = defaultdict(lambda: 1e-11, lm)

  def __call__(self, prefix):
    """
    Returns the probability of the last word conditioned on all previous ones.

    Args:
      prefix (str): The sentence prefix to be scored.
    """
    return self._model[prefix]


def greedy_decoder(ctc):
  """
  Performs greedy decoding (max decoding) on the output of a CTC network.

  Args:
    ctc (np.ndarray): The CTC output. Should be a 2D array (timesteps x alphabet_size)

  Returns:
    string: The decoded CTC output.
  """

  alphabet = list(ascii_lowercase) + [' ', '>']
  alphabet_size = len(alphabet)

  #  collapse repeating characters
  arg_max = np.argmax(ctc, axis=1)
  repeat_filter = arg_max[1:] != arg_max[:-1]
  repeat_filter = np.concatenate([[True], repeat_filter])
  collapsed = arg_max[repeat_filter]

  # discard blank tokens (the blank is always last in the alphabet)
  blank_filter = np.where(collapsed < (alphabet_size - 1))[0]
  final_sequence = collapsed[blank_filter]
  full_decode = ''.join([alphabet[letter_idx] for letter_idx in final_sequence])

  return full_decode[:full_decode.find('>')]

if __name__ == '__main__':
    lm = LanguageModel('language_model.p')
    for example_file in glob('examples/*.p'):
        example = pickle.load(open(example_file, 'rb'))

        t0 = time.time()
        before_lm = greedy_decoder(example)
        t_before_lm = time.time() - t0

        t0 = time.time()
        after_lm = prefix_beam_search(example, lm=lm)
        t_after_lm = time.time() - t0

        t0 = time.time()
        after_lm_log = prefix_beam_search_log_space(example, lm=lm, alpha=.5)
        t_after_lm_log = time.time() - t0

        print('\n\n{}'.format(example_file))
        print('BEFORE: {}sec, {}'.format(round(t_before_lm, 5), before_lm))
        print('AFTER(prob): {}sec, {}'.format(round(t_after_lm, 5), after_lm))
        print('AFTER(logp): {}sec, {}'.format(round(t_after_lm_log, 5), after_lm_log))
