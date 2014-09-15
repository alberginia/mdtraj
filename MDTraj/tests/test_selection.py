# #############################################################################
# MDTraj: A Python Library for Loading, Saving, and Manipulating
# Molecular Dynamics Trajectories.
# Copyright 2012-2014 Stanford University and the Authors
#
# Authors: Matthew Harrigan
# Contributors:
#
# MDTraj is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 2.1
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with MDTraj. If not, see <http://www.gnu.org/licenses/>.
# #############################################################################

import logging

import mdtraj
import numpy as np
from mdtraj.core.selection import SelectionParser
from mdtraj.testing import eq, get_fn


# Conda v2.0.1 build py34_0 spews a bunch of DeprecationWarnings
# from pyparsing internal code
logging.captureWarnings(True)

ala = mdtraj.load(get_fn("alanine-dipeptide-explicit.pdb"))


def test_simple():
    sp = SelectionParser("protein")
    eq(sp.unambiguous, 'Residue_is_protein')
    eq(sp.mdtraj_condition, "a.residue.is_protein")


def test_alias():
    sp = SelectionParser("waters")
    eq(sp.unambiguous, "Residue_is_water")
    eq(sp.mdtraj_condition, "a.residue.is_water")


def test_bool():
    sp = SelectionParser("protein or water")
    eq(sp.unambiguous, "(Residue_is_protein or Residue_is_water)")
    eq(sp.mdtraj_condition, "(a.residue.is_protein or a.residue.is_water)")

    sp.parse("protein or water or nucleic")
    eq(sp.unambiguous,
       "(Residue_is_protein or Residue_is_water or Residue_is_nucleic)")
    eq(sp.mdtraj_condition,
       "(a.residue.is_protein or a.residue.is_water or a.residue.is_nucleic)")

    sp.parse("protein and backbone")
    eq(sp.unambiguous, "(Residue_is_protein and Residue_is_backbone)")
    eq(sp.mdtraj_condition, "(a.residue.is_protein and a.residue.is_backbone)")

    sp.parse("protein && backbone")
    eq(sp.unambiguous, "(Residue_is_protein and Residue_is_backbone)")
    eq(sp.mdtraj_condition, "(a.residue.is_protein and a.residue.is_backbone)")


def test_nested_bool():
    sp = SelectionParser("protein and water or nucleic")
    eq(sp.mdtraj_condition,
       "((a.residue.is_protein and a.residue.is_water) or a.residue.is_nucleic)")

    sp.parse("protein and (water or nucleic)")
    eq(sp.mdtraj_condition,
       "(a.residue.is_protein and (a.residue.is_water or a.residue.is_nucleic))")


def test_values():
    sp = SelectionParser("resid 4")
    eq(sp.unambiguous, "Residue_index == 4")
    eq(sp.mdtraj_condition, "a.residue.index == 4")

    sp.parse("resid > 4")
    eq(sp.unambiguous, "Residue_index > 4")
    eq(sp.mdtraj_condition, "a.residue.index > 4")

    sp.parse("resid gt 4")
    eq(sp.unambiguous, "Residue_index > 4")
    eq(sp.mdtraj_condition, "a.residue.index > 4")

    sp.parse("resid 5 to 8")
    eq(sp.unambiguous, "Residue_index == range(5 to 8)")
    eq(sp.mdtraj_condition, "5 <= a.residue.index <= 8")


def test_not():
    sp = SelectionParser("not protein")
    eq(sp.unambiguous, "(not Residue_is_protein)")
    eq(sp.mdtraj_condition, "(not a.residue.is_protein)")

    sp.parse("not not protein")
    eq(sp.unambiguous, "(not (not Residue_is_protein))")
    eq(sp.mdtraj_condition, "(not (not a.residue.is_protein))")

    sp.parse('!protein')
    eq(sp.unambiguous, '(not Residue_is_protein)')
    eq(sp.mdtraj_condition, "(not a.residue.is_protein)")


def test_within():
    sp = SelectionParser("within 5 of backbone or sidechain")
    eq(sp.unambiguous,
       "(Atom_within == 5 of (Residue_is_backbone or Residue_is_sidechain))")


def test_quotes():
    should_be = "(a.name == 'O' and a.residue.name == 'ALA')"

    sp = SelectionParser("name O and resname ALA")
    eq(sp.mdtraj_condition, should_be)

    sp.parse('name "O" and resname ALA')
    eq(sp.mdtraj_condition, should_be)

    sp.parse("name 'O' and resname ALA")
    eq(sp.mdtraj_condition, should_be)


def test_top():
    prot = ala.topology.select("protein")
    eq(np.asarray(prot), np.arange(22))

    wat = ala.topology.select("water")
    eq(np.asarray(wat), np.arange(22, 2269))


def test_top_2():
    expr = ala.topology.select_expression("name O and water")
    eq(expr,
       "[a.index for a in top.atoms if (a.name == 'O' and a.residue.is_water)]")
